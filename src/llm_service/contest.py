import string
from fastapi import APIRouter, Depends
from sqlalchemy import insert, select, update, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from src.llm_service.models import contest, request_statistic, test_system, answer_question_system
from database.database import get_async_session
from src.auth.models import AuthUser, user
from src.llm_service.schemas import ContestResponse
from src.auth.auth_config import current_verified_user


CONTEST_DATAPK_ITM = 'DATAPK_ITM_VERSION_1_7'
CONTEST_DATAPK = 'DATAPK_VERSION_2_1'

router = APIRouter()


async def count_points(
    session: AsyncSession,
    current_user: AuthUser,
    filename: str,
    selected_option: str,
    right_answer: str,
    request_id: int
) -> int | float:
    if selected_option != right_answer:
        return 0

    receive_query = select(request_statistic.c.received_at).where(request_statistic.c.id == request_id)
    receive_test_time = (await session.execute(receive_query)).fetchone()[0]

    answer_query = select(test_system.c.answered_at, test_system.c.question).where(test_system.c.request_id == request_id)
    answer_test_time, req_que = (await session.execute(answer_query)).fetchone()

    request_ids_in_period = (await session.execute(
        select(request_statistic.c.id).where(
            and_(
                request_statistic.c.user_id == current_user.id,
                request_statistic.c.operation == 'get_answer',
                request_statistic.c.doc_name == filename,
                request_statistic.c.received_at < answer_test_time,
                request_statistic.c.received_at > receive_test_time
            )
        )
    )).fetchall()

    if not request_ids_in_period:
        return 1
    
    request_ids_in_period = list(map(lambda x: x[0], request_ids_in_period))

    questions_in_period = (await session.execute(
        select(answer_question_system.c.question).where(
            answer_question_system.c.request_id.in_(request_ids_in_period),
        )
    )).fetchall()

    questions_in_period = list(map(lambda x: x[0], questions_in_period))

    def normalize_string(s: str) -> str:
        return ''.join(char.lower() for char in s if char not in string.punctuation).replace(' ', '')
    
    def are_strings_equal(s1: str, s2: str) -> bool:
        return normalize_string(s1) == normalize_string(s2)
    
    for que in questions_in_period:
        if are_strings_equal(req_que, que):
            return 0.5
    
    return 1




async def fill_contest(
    session: AsyncSession,
    current_user: AuthUser,
    filename: str,
    selected_option: str,
    right_answer: str,
    request_id: int
) -> None:
    if filename not in (CONTEST_DATAPK_ITM, CONTEST_DATAPK):
        return
    
    existing_entry = (await session.execute(
        select(contest).where(
            and_(
                contest.c.user_id == current_user.id,
                contest.c.doc_name == filename
            )
        )
    )).fetchone()

    points_result = await count_points(session, current_user, filename, selected_option, right_answer, request_id)
        
    if not existing_entry:
        stmt = insert(contest).values(
            user_id=current_user.id,
            doc_name=filename,
            total_tests=1,
            cheat_tests=0 if points_result == int(points_result) else 1,
            test_feedbacks=0,
            answer_question_feedbacks=0,
            points=points_result
        )
        await session.execute(stmt)
        await session.commit()
    else:
        update_stmt = (
            update(contest)
            .where(
                and_(
                    contest.c.user_id == current_user.id,
                    contest.c.doc_name == filename
                ))
            .values(
                total_tests=contest.c.total_tests + 1,
                cheat_tests=contest.c.cheat_tests + (0 if points_result == int(points_result) else 1),
                points=contest.c.points + points_result
            )
        )
        await session.execute(update_stmt)
        await session.commit()
    return


async def get_full_leaderboard(session: AsyncSession, filename: str) -> list[ContestResponse]:
    query = (
        select(
            contest.c.user_id,
            contest.c.points,
            contest.c.total_tests,
            user.c.name,
            user.c.surname
        )
        .join(user, user.c.id == contest.c.user_id)
        .where(contest.c.doc_name == filename)
        .order_by(desc(contest.c.points))
    )
    
    records = (await session.execute(query)).fetchall()

    leaderboard = [
        ContestResponse(
            place=place,
            name=record.name,
            surname=record.surname,
            points=record.points,
            total_tests=record.total_tests
        )
        for place, record in enumerate(records, start=1)
    ]

    return leaderboard


@router.get(f"/leaderboard/{CONTEST_DATAPK_ITM}", response_model=list[ContestResponse])
async def get_datapk_itm_leaderboard(session: AsyncSession = Depends(get_async_session)) -> list[ContestResponse]:
    return await get_full_leaderboard(session, CONTEST_DATAPK_ITM)


@router.get(f"/leaderboard/{CONTEST_DATAPK}", response_model=list[ContestResponse])
async def get_datapk_itm_leaderboard(session: AsyncSession = Depends(get_async_session)) -> list[ContestResponse]:
    return await get_full_leaderboard(session, CONTEST_DATAPK)


async def get_my_leaderboard(
    session: AsyncSession,
    current_user: AuthUser,
    filename: str
) -> list[ContestResponse] | list[None]:
    query = (
        select(
            contest.c.user_id,
            contest.c.points,
            contest.c.total_tests,
            user.c.name,
            user.c.surname
        )
        .join(user, user.c.id == contest.c.user_id)
        .where(contest.c.doc_name == filename)
        .order_by(desc(contest.c.points))
    )

    records = (await session.execute(query)).fetchall()

    leaderboard = []
    user_record = None
    for place, record in enumerate(records, start=1):
        curr_record = ContestResponse(
            place=place,
            name=record.name,
            surname=record.surname,
            points=record.points,
            total_tests=record.total_tests
        )
        leaderboard.append(curr_record)
        if record.user_id == current_user.id:
            user_record = curr_record
    
    if user_record:
        user_place = leaderboard.index(user_record) + 1
        top_3 = leaderboard[:3]
        
        if user_place > 3:
            return top_3 + [user_record]
        else:
            return top_3
    else:
        return []
    

@router.get("/leaderboard_me")
async def get_my_leaderboards(
    session: AsyncSession = Depends(get_async_session),
    current_user: AuthUser = Depends(current_verified_user)
) -> dict:
    datapk_itm_leaderboard = await get_my_leaderboard(session, current_user, CONTEST_DATAPK_ITM)
    datapk_leaderboard = await get_my_leaderboard(session, current_user, CONTEST_DATAPK)

    return {'datapk_itm': {'doc_name': CONTEST_DATAPK_ITM, 'leaderboard': datapk_itm_leaderboard},
            'datapk': {'doc_name': CONTEST_DATAPK, 'leaderboard': datapk_leaderboard}}
