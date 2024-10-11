from datetime import datetime

from sqlalchemy import insert, select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from src.auth.models import AuthUser
from src.llm_service.models import request_statistic, feedback, test_system, answer_question_system
from src.llm_service.utils import convert_time
from src.services.celery_service import send_email
from config.config import SEND_ADMIN_NOTICES


async def add_statistic_row(
        current_user: AuthUser,
        operation: str,
        prompt_path: str,
        filename: str,
        tokens: int,
        embedding_tokens: int,
        total_time: float,
        metrics: list | None,
        gigachat_time: float,
        from_cache: bool,
        response: dict,
        session: AsyncSession
) -> int:
    try:
        stmt = insert(request_statistic).values(
            user_id=current_user.id,
            received_at=convert_time(datetime.now()),
            operation=operation,
            prompt_path=prompt_path,
            doc_name=filename,
            tokens=tokens,
            embedding_tokens=embedding_tokens,
            total_time=total_time,
            gigachat_time=gigachat_time,
            from_cache=from_cache
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
                generation_attempts=response['generation_attemps']
            )
        await session.execute(stmt)
        await session.commit()

        if SEND_ADMIN_NOTICES:
            DAILY_TOKEN_LIMIT = 63000

            start_of_day = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

            query = select(func.sum(request_statistic.c.tokens)).where(
                and_(
                    request_statistic.c.user_id == current_user.id,
                    request_statistic.c.received_at >= start_of_day
                )
            )
            spent_tokens_today = (await session.execute(query)).fetchone()[0]

            if spent_tokens_today >= DAILY_TOKEN_LIMIT and spent_tokens_today - tokens < DAILY_TOKEN_LIMIT:
                query = select(
                request_statistic.c.doc_name,
                func.sum(request_statistic.c.tokens).label('total_tokens')
                ).where(
                    and_(
                        request_statistic.c.user_id == current_user.id,
                        request_statistic.c.received_at >= start_of_day
                    )
                ).group_by(
                    request_statistic.c.doc_name
                )

                result = (await session.execute(query)).fetchall()
                tokens_by_doc_name = {row[0]: row[1] for row in result}

                send_email.delay(
                    name=current_user.name,
                    surname=current_user.surname,
                    user_email=current_user.email,
                    tokens_by_doc=tokens_by_doc_name,
                    destiny='token_limit'
                )

            if total_time > 15:
                if operation == 'get_answer':
                    send_email.delay(
                        filename=filename,
                        tokens=tokens, 
                        total_time=total_time, 
                        gigachat_time=gigachat_time, 
                        question=response['question'], 
                        answer=response['answer'],
                        destiny='qa_time_limit'
                    )
                elif operation == 'get_test':
                    send_email.delay(
                        filename=filename,
                        tokens=tokens, 
                        total_time=total_time, 
                        gigachat_time=gigachat_time,
                        generation_attemps=response['generation_attemps'],
                        question=response['question'],
                        options='<br>'.join([f'{i}) {response[f"{i} option"]}' for i in range(1, 5)]),
                        right_answer=response['right answer'],
                        destiny='test_time_limit'
                    )

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
