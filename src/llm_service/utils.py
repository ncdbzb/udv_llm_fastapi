import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from src.auth.models import user
from src.llm_service.schemas import ContestResponse
from src.llm_service.models import contest



async def send_data_to_llm(endpoint: str, data: dict):
    async with httpx.AsyncClient(timeout=150) as client:
        url = f"http://gigachat_api:8080/{endpoint}"
        response = await client.post(url, json=data)
        return response.json()
