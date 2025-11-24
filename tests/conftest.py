import pytest
from typing import AsyncGenerator, Generator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text
from redis.asyncio import Redis

# Testcontainers
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer

# Импорты приложения
from app.main import app
from app.db.base import Base
from app.api.deps import get_db, get_redis

# --- 1. КОНТЕЙНЕРЫ (SESSION SCOPE) ---

@pytest.fixture(scope="session")
def postgres_container() -> Generator[PostgresContainer, None, None]:
    with PostgresContainer("postgres:16-alpine", driver="asyncpg") as container:
        yield container

@pytest.fixture(scope="session")
def redis_container() -> Generator[RedisContainer, None, None]:
    with RedisContainer("redis:7-alpine") as container:
        yield container

# --- 2. POSTGRES ENGINE (FUNCTION SCOPE) ---

@pytest.fixture(scope="function")
async def db_engine(postgres_container):
    db_url = postgres_container.get_connection_url().replace("postgresql+psycopg2", "postgresql+asyncpg")
    engine = create_async_engine(db_url, echo=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    yield engine
    await engine.dispose()

# --- 3. REDIS CLIENT (FUNCTION SCOPE) ---

@pytest.fixture(scope="function")
async def redis_client(redis_container) -> AsyncGenerator[Redis, None]:
    host = redis_container.get_container_host_ip()
    port = redis_container.get_exposed_port(6379)
    
    client = Redis(host=host, port=port, decode_responses=True)
    
    await client.flushall()
    
    yield client
    await client.close()

# --- 4. DB SESSION (FUNCTION SCOPE) ---

@pytest.fixture(scope="function")
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    async_session = async_sessionmaker(db_engine, expire_on_commit=False)
    async with async_session() as session:
        yield session
        
        await session.rollback()

        async with session.begin():
            for table in reversed(Base.metadata.sorted_tables):
                await session.execute(text(f"TRUNCATE TABLE {table.name} RESTART IDENTITY CASCADE"))

# --- 5. HTTP CLIENT (FUNCTION SCOPE) ---

@pytest.fixture(scope="function")
async def client(db_session, redis_client) -> AsyncGenerator[AsyncClient, None]:
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_redis] = lambda: redis_client
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()