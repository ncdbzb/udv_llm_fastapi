from datetime import datetime

from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from src.llm_service.models import request_statistic, feedback


async def add_statistic_row(
        operation: str,
        prompt_path: str,
        tokens: int,
        total_time: float,
        metrics: list[int] | None,
        gigachat_time: float,
        session: AsyncSession
):
    try:
        stmt = insert(request_statistic).values(
            timestamp=datetime.now(),
            operation=operation,
            prompt_path=prompt_path,
            tokens=tokens,
            total_time=total_time,
            metrics=metrics,
            gigachat_time=gigachat_time
        )
        await session.execute(stmt)
        await session.commit()

        last_row = await session.execute(select(request_statistic).order_by(request_statistic.c.id.desc()).limit(1))
        last_id = last_row.scalar()
        return last_id
    except IntegrityError as e:
        print(e)


async def add_feedback_row(
        value: str,
        llm_response: str,
        user_comment: str,
        request_id: int,
        session: AsyncSession
):
    try:
        stmt = insert(feedback).values(
            value=value,
            llm_response=llm_response,
            user_comment=user_comment,
            request_id=request_id,
        )
        await session.execute(stmt)
        await session.commit()
        return {'status': 'added new feedback row'}
    except IntegrityError as e:
        print(e)
