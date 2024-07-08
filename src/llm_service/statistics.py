from datetime import datetime

from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from src.llm_service.models import request_statistic, feedback, test_system, answer_question_system
from src.llm_service.utils import convert_time


async def add_statistic_row(
        user_id: int,
        operation: str,
        prompt_path: str,
        filename: str,
        tokens: int,
        total_time: float,
        metrics: list | None,
        gigachat_time: float,
        response: dict,
        session: AsyncSession
) -> int:
    try:
        stmt = insert(request_statistic).values(
            user_id=user_id,
            received_at=convert_time(datetime.now()),
            operation=operation,
            prompt_path=prompt_path,
            doc_name=filename,
            tokens=tokens,
            total_time=total_time,
            gigachat_time=gigachat_time
        )
        await session.execute(stmt)
        await session.commit()

        last_row = await session.execute(select(request_statistic).order_by(request_statistic.c.id.desc()).limit(1))
        last_id = last_row.scalar()

        if metrics:
            stmt = insert(answer_question_system).values(
                request_id=last_id,
                question=response['question'],
                answer=response['answer'],
                metrics=metrics
            )
        else:
            stmt = insert(test_system).values(
                request_id=last_id,
                question=response['question'],
                option_1=response['1 option'],
                option_2=response['2 option'],
                option_3=response['3 option'],
                option_4=response['4 option'],
                right_answer=response['right answer'],
            )
        await session.execute(stmt)
        await session.commit()

        return last_id
    except IntegrityError as e:
        print(e)


async def add_feedback_row(
        value: str,
        user_comment: str,
        request_id: int,
        session: AsyncSession
):
    try:
        stmt = insert(feedback).values(
            value=value,
            user_comment=user_comment,
            request_id=request_id,
        )
        await session.execute(stmt)
        await session.commit()
        return {'status': 'added new feedback row'}
    except IntegrityError as e:
        print(e)
