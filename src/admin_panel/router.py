from fastapi import APIRouter, Depends
from fastapi_users.jwt import generate_jwt
from sqlalchemy.ext.asyncio import AsyncSession

from database.database import get_async_session
from src.auth.models import AuthUser
from src.admin_panel.models import admin_requests
from src.auth.send_email import send_email
from sqlalchemy import select, update, func
from src.auth.auth_config import current_superuser
from src.llm_service.models import request_statistic, feedback
from config.config import SECRET_MANAGER as verification_token_secret


router = APIRouter()


@router.get('/requests')
async def get_admin_panel(
        user: AuthUser = Depends(current_superuser),
        session: AsyncSession = Depends(get_async_session)
):
    query = select(admin_requests.c.info).where(admin_requests.c.status == 'approval')
    result = await session.execute(query)

    return result.mappings().all()


@router.post('/reject')
async def reject_request(
        request_id: int,
        user: AuthUser = Depends(current_superuser),
        session: AsyncSession = Depends(get_async_session)
):
    query = select(admin_requests).where(admin_requests.c.id == int(request_id))
    result = await session.execute(query)
    info = result.fetchone().info

    await send_email(name=info.get('name'), user_email=info.get('email'), token='', destiny='reject')

    stmt = update(admin_requests).where(admin_requests.c.id == int(request_id)).values(status='rejected')
    await session.execute(stmt)
    await session.commit()

    return {'status': f'request #{request_id} has been rejected successfully'}


@router.post('/accept')
async def accept_request(
        request_id: int,
        user: AuthUser = Depends(current_superuser),
        session: AsyncSession = Depends(get_async_session)
):
    query = select(admin_requests).where(admin_requests.c.id == int(request_id))
    result = await session.execute(query)
    values = result.fetchone()
    info = values.info

    user_email = info.get('email')

    token_data = {
            "sub": str(values.user_id),
            "email": user_email,
            "aud": "fastapi-users:verify",
        }
    token = generate_jwt(
        token_data,
        verification_token_secret,
        3600,
    )

    await send_email(name=info.get('name'), user_email=user_email, token=token, destiny='accept')

    stmt = update(admin_requests).where(admin_requests.c.id == int(request_id)).values(status='accepted')
    await session.execute(stmt)
    await session.commit()

    return {'status': f'request #{request_id} has been accepted successfully'}


@router.post('/get_feedback')
async def get_feedback(
        all: bool,
        user: AuthUser = Depends(current_superuser),
        session: AsyncSession = Depends(get_async_session)
):
    if all:
        query = select(feedback)
        result = await session.execute(query)
    else:
        query = select(feedback).where(feedback.c.viewed == False)
        result = await session.execute(query)

    return result.mappings().all()


@router.post('/set_viewed')
async def set_viewed(
        feedback_id: int,
        user: AuthUser = Depends(current_superuser),
        session: AsyncSession = Depends(get_async_session)
):
    stmt = update(feedback).where(feedback.c.id == int(feedback_id)).values(viewed=True)
    await session.execute(stmt)
    await session.commit()

    return {'status': f'feedback #{feedback_id} was viewed'}

@router.post('/get_tokens')
async def get_tokens(
        operation: str,
        user: AuthUser = Depends(current_superuser),
        session: AsyncSession = Depends(get_async_session)
):
    if operation in ('get_test', 'get_answer'):
        query = select(func.sum(request_statistic.c.tokens)).where(request_statistic.c.operation == operation)
        result = await session.execute(query)
    elif operation == 'both':
        query = select(func.sum(request_statistic.c.tokens))
        result = await session.execute(query)
    else:
        raise ValueError("Unexpected operation")
    
    return result.scalar()