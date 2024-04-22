from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database.database import get_async_session
from src.auth.models import AuthUser
from src.llm_service.schemas import Feedback
from src.llm_service.utils import send_data_to_llm
from src.docs.models import doc
from src.llm_service.statistics import add_statistic_row, add_feedback_row
from src.auth.auth_config import current_verified_user

router = APIRouter()


@router.post("/get_answer")
async def send_data(
        filename: str,
        question: str,
        session: AsyncSession = Depends(get_async_session)
):
    data = {'filename': filename,
            'question': question}
    
    query = select(doc).where(doc.c.name == filename)
    result = await session.execute(query)
    if not result.fetchone():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document with this name was not found")
    
    response = await send_data_to_llm('process_questions', data)
    request_id = await add_statistic_row(
        operation='get_answer',
        prompt_path=response['prompt_path'],
        tokens=response['tokens'],
        total_time=response['total_time'],
        metrics=response['metrics'],
        gigachat_time=response['gigachat_time'],
        session=session
    )
    # result = {'result': response['result'],
    #           'request_id': request_id}
    result = response['result']
    result['request_id'] = request_id
    return result


@router.post("/get_test")
async def send_data(
        filename: str,
        # user: AuthUser = Depends(current_verified_user),
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
        session=session
    )
    result = response['result']
    result['request_id'] = request_id
    return result


@router.post("/send_feedback")
async def send_feedback(
        feedback: Feedback,
        session: AsyncSession = Depends(get_async_session)
):
    await add_feedback_row(
        value=feedback.value,
        llm_response=feedback.llm_response,
        user_comment=feedback.user_comment,
        request_id=feedback.request_id,
        session=session
    )
    return {"result": "feedback added successfully"}

