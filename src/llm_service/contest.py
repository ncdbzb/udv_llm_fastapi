from sqlalchemy import insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.models import AuthUser
from src.llm_service.models import contest


async def fill_contest(
    session: AsyncSession,
    user: AuthUser,
    selected_option: str,
    right_answer: str
) -> None:
    existing_entry = (await session.execute(select(contest).where(contest.c.user_id == user.id))).fetchone()
    
    if not existing_entry:
        stmt = insert(contest).values(
            user_id=user.id,
            total_tests=1,
            points=1 if selected_option == right_answer else 0
        )
        await session.execute(stmt)
        await session.commit()
    else:
        update_stmt = (
            update(contest)
            .where(contest.c.user_id == user.id)
            .values(
                total_tests=contest.c.total_tests + 1,
                points=contest.c.points + (1 if selected_option == right_answer else 0)
            )
        )
        await session.execute(update_stmt)
        await session.commit()
    return
    