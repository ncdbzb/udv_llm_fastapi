from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, update

from database.database import get_async_session
from src.llm_service.contest import fill_contest, CONTEST_DATAPK, CONTEST_DATAPK_ITM
from src.auth.models import AuthUser
from src.llm_service.schemas import Feedback, CheckTest
from src.llm_service.utils import send_data_to_llm, convert_time
from src.docs.models import doc
from src.llm_service.models import contest
from src.llm_service.models import test_system, request_statistic
from src.llm_service.statistics import add_statistic_row, add_feedback_row
from src.auth.auth_config import current_verified_user

router = APIRouter()


@router.post("/get_answer")
async def send_data(
    filename: str,
    question: str,
    current_user: AuthUser = Depends(current_verified_user),
    session: AsyncSession = Depends(get_async_session)
):
    data = {'filename': filename,
            'question': question}
    
    query = select(doc).where(doc.c.name == filename)
    if not (await session.execute(query)).fetchone():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document with this name was not found")
    
    response = await send_data_to_llm('process_questions', data)
    request_id = await add_statistic_row(
        current_user=current_user,
        operation='get_answer',
        prompt_path=response['prompt_path'],
        filename=filename,
        tokens=response['tokens'],
        embedding_tokens=response['embedding_tokens'],
        total_time=response['total_time'],
        metrics=response['metrics'],
        gigachat_time=response['gigachat_time'],
        from_cache=response['from_cache'],
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
    current_user: AuthUser = Depends(current_verified_user),
    session: AsyncSession = Depends(get_async_session)
):
    data = {'filename': filename}
    response = await send_data_to_llm('process_data', data)
    request_id = await add_statistic_row(
        current_user=current_user,
        operation='get_test',
        prompt_path=response['prompt_path'],
        filename=filename,
        tokens=response['tokens'],
        embedding_tokens=0,
        total_time=response['total_time'],
        metrics=None,
        gigachat_time=response['gigachat_time'],
        from_cache=False,
        response=response['result']['result'],
        session=session
    )
    result = response['result']
    result['request_id'] = request_id
    del result['result']['right answer']
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
            test_system.c.answered_at.is_(None)
        )
    )
    current_answer = (await session.execute(query)).fetchone()
    if not current_answer:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Question is not exist or already answered')
    
    query = select(
        request_statistic.c.doc_name
    ).where(
        request_statistic.c.id == check_data.request_id
    )
    doc_name = (await session.execute(query)).fetchone()[0]

    update_stmt = update(
        test_system
    ).where(
        test_system.c.request_id == check_data.request_id
    ).values(
        answered_at=convert_time(datetime.now())
    )

    await session.execute(update_stmt)
    await session.commit()

    await fill_contest(session, user, doc_name, check_data.selected_option, current_answer[0], check_data.request_id)

    return {'right_answer': current_answer[0]}


@router.post("/send_feedback")
async def send_feedback(
    feedback: Feedback,
    current_user: AuthUser = Depends(current_verified_user),
    session: AsyncSession = Depends(get_async_session)
):
    await add_feedback_row(
        value=feedback.value,
        user_comment=feedback.user_comment,
        request_id=feedback.request_id,
        session=session
    )

    existing_entry = (await session.execute(
        select(request_statistic.c.operation, request_statistic.c.doc_name).where(
            and_(
                request_statistic.c.id == feedback.request_id,
                request_statistic.c.doc_name.in_((CONTEST_DATAPK, CONTEST_DATAPK_ITM))
            )
        )
    )).fetchone()

    if existing_entry:
        operation, filename = existing_entry[0], existing_entry[1]
        update_data = {}
        if operation == 'get_test':
            update_data['test_feedbacks'] = contest.c.test_feedbacks + 1
        elif operation == 'get_answer':
            update_data['answer_question_feedbacks'] = contest.c.answer_question_feedbacks + 1

        update_stmt = (
            update(contest)
            .where(
                and_(
                    contest.c.user_id == current_user.id,
                    contest.c.doc_name == filename
                ))
            .values(**update_data)
        )
        await session.execute(update_stmt)
        await session.commit()

    return {"result": "feedback added successfully"}
