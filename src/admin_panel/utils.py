from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from src.admin_panel.schemas import admin_request_schema
from src.admin_panel.models import admin_requests


async def add_admin_request(
        user: admin_request_schema,
        session: AsyncSession
):
    info = {
        'name': user.name,
        'surname': user.surname,
        'email': user.email
    }

    try:
        stmt = insert(admin_requests).values(timestamp=datetime.now(), info=info, status='approval', user_id=user.id)
        await session.execute(stmt)
        await session.commit()
        return {'status': 'added new admin request'}
    except IntegrityError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="You have already sent the request")
