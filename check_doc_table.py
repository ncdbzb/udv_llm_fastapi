import asyncio
import httpx

from src.docs.utils import request_get_actual_doc_list
from src.docs.models import doc
from sqlalchemy import select, delete, insert
from database.database import async_session_maker


async def check_doc_table():
    for _ in range(5):
        try:
            actual_doc_list = await request_get_actual_doc_list()
            if actual_doc_list:
                break
        except httpx.ConnectError:
            await asyncio.sleep(1)
    else:
        raise asyncio.TimeoutError('Something went wrong')
    async with async_session_maker() as session:
        query = select(doc.c.name)
        result = await session.execute(query)

        db_doc_list = [row for row in result.scalars().all()]    

        db_set = set(db_doc_list)
        actual_set = set(actual_doc_list)

        add_doc_list = list(actual_set - db_set)
        del_doc_list = list(db_set - actual_set)

        if not (add_doc_list or del_doc_list):
            print('Doc table initialized succefully')
            return
 
        if del_doc_list:
            delete_stmt = delete(doc).where(doc.c.name.in_(del_doc_list))
            await session.execute(delete_stmt)
            await session.commit()
            print(f'Documents {del_doc_list} were deleted from db')

        if add_doc_list:
            add_stmt = insert(doc).values(
                [
                    {'name': name, 'description': 'data', 'user_id': None}
                    for name in add_doc_list
                ]
            )
            await session.execute(add_stmt)
            await session.commit()
            print(f'Documents {add_doc_list} were added to db')
