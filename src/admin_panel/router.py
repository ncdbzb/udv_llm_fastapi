from fastapi import APIRouter, Depends
from fastapi_users.jwt import generate_jwt
from sqlalchemy.ext.asyncio import AsyncSession

from database.database import get_async_session
from src.auth.models import AuthUser
from src.admin_panel.models import admin_requests
from src.auth.send_email import send_email
from src.admin_panel.utils import add_admin_request
from src.admin_panel.schemas import admin_request_schema
from sqlalchemy import select, update
from src.auth.auth_config import current_superuser
from config.config import SECRET_MANAGER as verification_token_secret


router = APIRouter()


@router.get('/requests')
async def get_admin_panel(
        user: AuthUser = Depends(current_superuser),
        session: AsyncSession = Depends(get_async_session)
):
    query = select(admin_requests)
    result = await session.execute(query)

    return result.mappings().all()


@router.post('/reject')
async def reject_request(
        request_id: int,
        user: AuthUser = Depends(current_superuser),
        session: AsyncSession = Depends(get_async_session)
):
    query = select(admin_requests).where(admin_requests.c.request_id == int(request_id))
    result = await session.execute(query)
    info = result.fetchone().info

    await send_email(name=info.get('name'), user_email=info.get('email'), token='', destiny='reject')

    stmt = update(admin_requests).where(admin_requests.c.request_id == int(request_id)).values(status='rejected')
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


@router.post('/send-request')
async def send_request(
        auth_user: admin_request_schema,
        session: AsyncSession = Depends(get_async_session)
):
    await add_admin_request(auth_user, session=session)
    return {'status': 'add new request to table'}