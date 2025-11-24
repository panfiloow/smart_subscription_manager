import pytest
from httpx import AsyncClient
from redis import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

# Тест 1: Проверяем, что приложение вообще живое
@pytest.mark.asyncio
async def test_root(client: AsyncClient):
    response = await client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Subscription Manager API is running"}

# Тест 2: Проверяем, что база данных работает (делаем SELECT 1)
@pytest.mark.asyncio
async def test_db_connection(db_session: AsyncSession):
    result = await db_session.execute(text("SELECT 1"))
    assert result.scalar() == 1

# Тест 3: Redis
@pytest.mark.asyncio
async def test_redis_connection(redis_client: Redis):
    await redis_client.set("test_key", "hello_redis")
    
    value = await redis_client.get("test_key")
    
    assert value == "hello_redis"