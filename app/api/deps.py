from typing import Annotated, AsyncGenerator
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
import jwt
from redis import Redis
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.exceptions import TokenExpiredException
from app.db.session import AsyncSessionLocal
from app.models.user import User
from app.repositories.subscription_repository import SubscriptionRepository
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService
from app.services.subscription_service import SubscriptionService
from app.core.redis import redis_pool
from redis import asyncio as aioredis

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


async def get_redis() -> AsyncGenerator[aioredis.Redis, None]:
    """
    Dependency для получения клиента Redis.
    Использует пул соединений.
    """
    client = aioredis.Redis(connection_pool=redis_pool)
    try:
        yield client
    finally:
        await client.close()


def get_user_repository(session: AsyncSession = Depends(get_db)) -> UserRepository:
    return UserRepository(session)


def get_auth_service(
    user_repo: UserRepository = Depends(get_user_repository),
    redis: aioredis.Redis = Depends(get_redis),
) -> AuthService:
    return AuthService(user_repo, redis)


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    user_repo: UserRepository = Depends(get_user_repository),
    redis: aioredis.Redis = Depends(get_redis),
) -> User:

    is_blacklisted = await redis.get(f"blacklist:{token}")
    if is_blacklisted:
        raise TokenExpiredException()

    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        username: str = payload.get("sub")
        if username is None:
            raise TokenExpiredException()
    except jwt.InvalidTokenError:
        raise TokenExpiredException()

    user = await user_repo.get_by_email(email=username)

    if user is None:
        raise TokenExpiredException()

    return user


def get_subscription_repository(
    session: AsyncSession = Depends(get_db),
) -> SubscriptionRepository:
    return SubscriptionRepository(session)


def get_subscription_service(
    sub_repo: SubscriptionRepository = Depends(get_subscription_repository),
    redis: Redis = Depends(get_redis),
) -> SubscriptionService:
    return SubscriptionService(sub_repo, redis)
