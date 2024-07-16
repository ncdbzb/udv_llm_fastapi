import httpx
import ipaddress
import re
from fastapi import HTTPException, status


async def send_file_to_llm(file_path: str):
    async with httpx.AsyncClient() as client:
        url = "http://gigachat_api:8080/process_doc"
        with open(file_path, "rb") as file:
            files = {"file": (file.name.split('/')[-1], file, "application/octet-stream")}
            response = await client.post(url, files=files, timeout=150)
            return response.json()


async def request_delete_doc(doc_name: str):
    async with httpx.AsyncClient() as client:
        url = "http://gigachat_api:8080/process_delete_doc"
        response = await client.post(url, json={'doc_name': doc_name}, timeout=10)
        return response.json()
    

async def request_get_actual_doc_list():
    async with httpx.AsyncClient() as client:
        url = "http://gigachat_api:8080/process_get_actual_doc_list"
        response = await client.post(url, timeout=10)
        return response.json()
    

async def request_change_doc_name(cur_name: str, new_name: str):
    async with httpx.AsyncClient() as client:
        url = "http://gigachat_api:8080/process_change_doc_name"
        response = await client.post(url, json={'cur_name': cur_name, 'new_name': new_name}, timeout=10)
        return response.json()
    

async def request_add_data(file_path: str):
    async with httpx.AsyncClient() as client:
        url = "http://gigachat_api:8080/process_add_data"
        with open(file_path, "rb") as file:
            files = {"file": (file.name.split('/')[-1], file, "application/octet-stream")}
            response = await client.post(url, files=files, timeout=60)
            return response.json()


def is_valid_filename(filename: str) -> bool:
    # 1. Contains 3-63 characters
    if not (3 <= len(filename) <= 63):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Filename must contain between 3 and 63 characters.")
    
    # 2. Starts and ends with an alphanumeric character
    if not (filename[0].isalnum() and filename[-1].isalnum()):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Filename must start and end with an alphanumeric character.")
    
    # 3. Contains only alphanumeric characters, underscores or hyphens (-)
    if not re.match(r'^[a-zA-Z0-9_-]*$', filename):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Filename can only contain alphanumeric characters, underscores, or hyphens (-).")
    
    # 4. Contains no two consecutive periods (..)
    if '..' in filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Filename must not contain two consecutive periods (..).")
    
    # 5. Is not a valid IPv4 address
    try:
        ipaddress.IPv4Address(filename)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Filename must not be a valid IPv4 address.")
    except ipaddress.AddressValueError:
        pass
    
    return True
