import asyncio
import os
import shutil

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from sqlalchemy import insert, select, delete, update, or_
from sqlalchemy.ext.asyncio import AsyncSession

from config.logs import doc_info
from src.auth.auth_config import current_verified_user, current_superuser
from src.auth.models import AuthUser
from src.docs.schemas import ChangeDoc
from database.database import get_async_session
from src.docs.models import doc
from src.docs.utils import send_file_to_llm, request_delete_doc, is_valid_filename, request_change_doc_name, request_add_data

router = APIRouter()


@router.post(
    '/upload-dock',
    status_code=status.HTTP_202_ACCEPTED,
)
async def upload_form(
    dock_name: str,
    dock_description: str,
    file: UploadFile = File(...),
    user: AuthUser = Depends(current_superuser),
    session: AsyncSession = Depends(get_async_session)
):
    is_valid_filename(dock_name)
    extension = file.filename.split('.')[-1]

    if extension not in ('zip', 'txt'):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File has an unsupported extension")
    
    doc_exist = select(doc).where(doc.c.name == dock_name)
    if (await session.execute(doc_exist)).fetchone():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Document with this name already exists")
    
    try:
        new_name = f"{dock_name}.{extension}"
        file_path = f"src/docs/temp/{new_name}"

        with open(file_path, "wb") as file_object:
            shutil.copyfileobj(file.file, file_object)
        
        doc_info.debug(f'new file {new_name} saved at {file_path}')

        response = await send_file_to_llm(file_path)
        
        if response['result'] == 'success':
            stmt = insert(doc).values(
                name=dock_name,
                type=extension,
                chunk_size=response['info']['chunk_size'],
                embedding_model=response['info']['embedding_model'],
                description=dock_description,
                user_id=user.id)
            await session.execute(stmt)
            await session.commit()

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await asyncio.to_thread(os.remove, file_path)
        doc_info.debug(f'new file {new_name} has been deleted from {file_path}')

    return {'status': 'added new doc'}


@router.get(
    '/my',
    status_code=status.HTTP_200_OK,
)
async def get_my_docs(
    user: AuthUser = Depends(current_verified_user),
    session: AsyncSession = Depends(get_async_session)
):
    query = select(doc.c.name, doc.c.description).where(or_(doc.c.user_id == int(user.id), doc.c.in_contest == True))
    result = await session.execute(query)

    return result.mappings().all()


@router.patch(
    '/change_data',
    status_code=status.HTTP_204_NO_CONTENT
)
async def change_doc(
    change_data: ChangeDoc,
    user: AuthUser = Depends(current_verified_user),
    session: AsyncSession = Depends(get_async_session),
):
    query = select(doc.c.name, doc.c.description, doc.c.user_id).where(
        doc.c.name == change_data.current_name)
    current_data = (await session.execute(query)).fetchone()

    if not current_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document with this name was not found")
    
    cur_name, cur_descriprion, cur_user_id = current_data

    if not user.is_superuser and user.id != cur_user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Forbidden")
    
    update_values = {}
    if change_data.new_name and change_data.new_name != cur_name and is_valid_filename(change_data.new_name):
        update_values['name'] = change_data.new_name
        await request_change_doc_name(cur_name, change_data.new_name)
    if change_data.description and change_data.description != cur_descriprion:
        update_values['description'] = change_data.description

    if update_values:
        update_query = update(doc).where(doc.c.name == change_data.current_name).values(**update_values)
        await session.execute(update_query)
        await session.commit()

    return


@router.post(
    '/add_data',
    status_code=status.HTTP_204_NO_CONTENT,
)
async def add_data(
    doc_name: str,
    file: UploadFile = File(...),
    user: AuthUser = Depends(current_verified_user),
    session: AsyncSession = Depends(get_async_session)
):
    query = select(doc.c.user_id).where(doc.c.name == doc_name)
    cur_user_id = (await session.execute(query)).fetchone()[0]

    if not cur_user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document with this name was not found")

    if not user.is_superuser and user.id != cur_user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Forbidden")
    
    extension = file.filename.split('.')[-1]
    if extension not in ('txt'):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File has an unsupported extension")
    
    try:
        new_name = f"{doc_name}.{extension}"
        file_path = f"src/docs/temp/{new_name}"

        with open(file_path, "wb") as file_object:
            shutil.copyfileobj(file.file, file_object)
        
        doc_info.debug(f'add data file {new_name} saved at {file_path}')

        await request_add_data(file_path)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await asyncio.to_thread(os.remove, file_path)
        doc_info.debug(f'add data file {new_name} has been deleted from {file_path}')


@router.get(
    '/all',
    status_code=status.HTTP_200_OK,
)
async def get_all_docs(
    session: AsyncSession = Depends(get_async_session),
    user: AuthUser = Depends(current_superuser)
):
    my_docs = await session.execute(select(doc.c.name, doc.c.description))

    return my_docs.mappings().all()


@router.delete(
    '/delete-my',
    name="docs:delete_doc",
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Missing token or inactive user.",
        },
        status.HTTP_403_FORBIDDEN: {
            "description": "Not verified or not company representative.",
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "The doc does not exist.",
        },
    },
)
async def del_my_docs(
    doc_name: str,
    user: AuthUser = Depends(current_verified_user),
    session: AsyncSession = Depends(get_async_session)
) -> None:
    query = select(doc).where(doc.c.name == doc_name)
    result = await session.execute(query)

    # Проверка наличия документа
    if not result.mappings().all():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="The doc does not exist.")

    # Проверка, что текущий пользователь является владельцем документа
    if not user.is_superuser:
        query = select(doc.c.user_id).where(doc.c.name == doc_name)
        result = await (session.execute(query))
        check_owner = result.mappings().one()['user_id']
        if check_owner != user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Forbidden")

    try:
        stmt = delete(doc).where(doc.c.name == doc_name)
        await session.execute(stmt)
        await session.commit()

        response = await request_delete_doc(doc_name)
        return(response)
    except Exception as e:
        print(e)
