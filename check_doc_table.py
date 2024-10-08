import asyncio
import httpx

from src.docs.utils import request_get_actual_doc_list
from src.docs.models import doc
from src.auth.models import user
from sqlalchemy import select, delete, insert
from database.database import async_session_maker
from config.config import admin_dict
from config.logs import doc_info


async def check_doc_table():
    for _ in range(5):
        try:
            actual_doc_list = await request_get_actual_doc_list()
            if actual_doc_list:
                break
        except httpx.ConnectError as e:
            doc_info.error(e)
            await asyncio.sleep(5)
    else:
        raise asyncio.TimeoutError('Something went wrong')
    async with async_session_maker() as session:
        result = await session.execute(select(doc.c.name))

        db_doc_list = [row for row in result.scalars().all()]    

        db_set = set(db_doc_list)
        actual_set = set(actual_doc_list)

        add_doc_list = list(actual_set - db_set)
        del_doc_list = list(db_set - actual_set)

        if not (add_doc_list or del_doc_list):
            doc_info.debug('Doc table initialized succefully')
            return
 
        if del_doc_list:
            delete_stmt = delete(doc).where(doc.c.name.in_(del_doc_list))
            await session.execute(delete_stmt)
            await session.commit()
            doc_info.info(f'Documents {del_doc_list} were deleted from db')

        result = (await session.execute(select(user.c.id).where(user.c.email == admin_dict['email']))).fetchone()
        admin_id = result[0] if result else None
        if not admin_id:
            doc_info.warning(f'Documents got {admin_id} in \"user_id\" field!')

        if add_doc_list:
            add_stmt = insert(doc).values(
                [
                    {'name': name, 'description': 'data', 'user_id': admin_id}
                    for name in add_doc_list
                ]
            )
            await session.execute(add_stmt)
            await session.commit()
            doc_info.info(f'Documents {add_doc_list} were added to db')
