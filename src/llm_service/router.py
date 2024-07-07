from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, update, desc

from database.database import get_async_session
from src.llm_service.contest import fill_contest
from src.auth.models import AuthUser, user
from src.llm_service.schemas import Feedback, CheckTest, ContestResponse
from src.llm_service.utils import send_data_to_llm
from src.docs.models import doc
from src.llm_service.models import test_system, contest
from src.llm_service.statistics import add_statistic_row, add_feedback_row
from src.auth.auth_config import current_verified_user

router = APIRouter()


@router.post("/get_answer")
async def send_data(
    filename: str,
    question: str,
    user: AuthUser = Depends(current_verified_user),
    session: AsyncSession = Depends(get_async_session)
):
    data = {'filename': filename,
            'question': question}
    
    query = select(doc).where(doc.c.name == filename)
    if not (await session.execute(query)).fetchone():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document with this name was not found")
    
    response = await send_data_to_llm('process_questions', data)
    request_id = await add_statistic_row(
        operation='get_answer',
        prompt_path=response['prompt_path'],
        tokens=response['tokens'],
        total_time=response['total_time'],
        metrics=response['metrics'],
        gigachat_time=response['gigachat_time'],
        response=response['result'],
        session=session
    )
    result = {'result': response['result'],
              'request_id': request_id}
    # result = response['result']
    # result['request_id'] = request_id
    return result


@router.post("/get_test")
async def send_data(
    filename: str,
    user: AuthUser = Depends(current_verified_user),
    session: AsyncSession = Depends(get_async_session)
):
    data = {'filename': filename}
    response = await send_data_to_llm('process_data', data)
    request_id = await add_statistic_row(
        operation='get_test',
        prompt_path=response['prompt_path'],
        tokens=response['tokens'],
        total_time=response['total_time'],
        metrics=None,
        gigachat_time=response['gigachat_time'],
        response=response['result']['result'],
        session=session
    )
    result = response['result']
    result['request_id'] = request_id
    return result


@router.post("/check_test")
async def check_test(
    check_data: CheckTest,
    user: AuthUser = Depends(current_verified_user),
    session: AsyncSession = Depends(get_async_session)
):

    query = select(
        test_system.c.right_answer
    ).where(
        and_(      
            test_system.c.request_id == check_data.request_id,
            test_system.c.is_answered == False
        )
    )
    current_answer = (await session.execute(query)).fetchone()
    if not current_answer:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Questions is not exist or already answered')

    await fill_contest(session, user, check_data.selected_option, current_answer[0])

    update_stmt = update(
        test_system
    ).where(
        test_system.c.request_id == check_data.request_id
    ).values(
        is_answered=True
    )

    await session.execute(update_stmt)
    await session.commit()

    return {'right_answer': current_answer[0]}


@router.post("/send_feedback")
async def send_feedback(
    feedback: Feedback,
    user: AuthUser = Depends(current_verified_user),
    session: AsyncSession = Depends(get_async_session)
):
    await add_feedback_row(
        value=feedback.value,
        user_comment=feedback.user_comment,
        request_id=feedback.request_id,
        session=session
    )
    return {"result": "feedback added successfully"}


@router.get("/contest/leaderboard", response_model=list[ContestResponse])
async def get_full_leaderboard(session: AsyncSession = Depends(get_async_session)) -> list[ContestResponse]:
    query = (
        select(
            contest.c.user_id,
            contest.c.points,
            contest.c.total_tests,
            user.c.name,
            user.c.surname
        )
        .join(user, user.c.id == contest.c.user_id)
        .order_by(desc(contest.c.points))
    )
    
    result = await session.execute(query)
    records = result.fetchall()

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


@router.get("/contest/leaderboard/me", response_model=list[ContestResponse])
async def get_full_leaderboard(
    session: AsyncSession = Depends(get_async_session),
    current_user: AuthUser = Depends(current_verified_user)
    ) -> list[ContestResponse]:
    query = (
        select(
            contest.c.user_id,
            contest.c.points,
            contest.c.total_tests,
            user.c.name,
            user.c.surname
        )
        .join(user, user.c.id == contest.c.user_id)
        .order_by(desc(contest.c.points))
    )
    
    result = await session.execute(query)
    records = result.fetchall()

    leaderboard = []
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
        return leaderboard[:3]
    