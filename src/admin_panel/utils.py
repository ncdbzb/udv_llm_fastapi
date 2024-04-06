from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select

from src.admin_panel.schemas import admin_request_schema
from src.admin_panel.models import admin_requests
from src.auth.models import user

async def add_admin_request(
        auth_user: admin_request_schema,
        session: AsyncSession
):
    query = select(user).where(user.c.email == auth_user.email)
    result = await session.execute(query)
    user_row = result.fetchone()

    try:
        info = {
            'name': user_row.name,
            'surname': user_row.surname,
            'email': auth_user.email,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    try:
        stmt = insert(admin_requests).values(timestamp=datetime.now(), info=info, status='approval', user_id=user_row.id)
        await session.execute(stmt)
        await session.commit()
        return {'status': 'added new admin request'}
    except IntegrityError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="You have already sent the request")
