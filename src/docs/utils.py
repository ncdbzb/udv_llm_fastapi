import httpx


async def send_file_to_llm(file_path: str):
    async with httpx.AsyncClient() as client:
        url = "http://gigachat_api:8080/process_doc"
        with open(file_path, "rb") as file:
            files = {"file": (file.name.split('/')[-1], file, "application/octet-stream")}
            response = await client.post(url, files=files, timeout=150)
            print(response.text)
            return response.json()


async def request_delete_doc(doc_name: int):
    async with httpx.AsyncClient() as client:
        url = "http://gigachat_api:8080/process_delete_doc"
        response = await client.post(url, json={'doc_name': doc_name}, timeout=10)
        return response.json()
    

async def request_get_actual_doc_list():
    async with httpx.AsyncClient() as client:
        url = "http://gigachat_api:8080/process_get_actual_doc_list"
        response = await client.post(url, timeout=10)
        return response.json()
