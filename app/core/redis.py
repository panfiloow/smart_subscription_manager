from redis import asyncio as aioredis
from app.core.config import settings

redis_pool = aioredis.ConnectionPool.from_url(
    settings.REDIS_URL, encoding="utf-8", decode_responses=True
)
