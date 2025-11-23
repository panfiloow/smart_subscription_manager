from fastapi import HTTPException, status
from datetime import datetime, timedelta, timezone

import jwt
from redis import Redis
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate
from app.schemas.token import Token
from app.core import security
from app.core.config import settings


class AuthService:
    def __init__(self, user_repo: UserRepository, redis: Redis):
        self.user_repo = user_repo
        self.redis = redis

    async def register_user(self, user_in: UserCreate):
        existing_user = await self.user_repo.get_by_email(user_in.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            )

        hashed_password = security.get_password_hash(user_in.password)

        user = await self.user_repo.create(user_in, hashed_password)
        await self.user_repo.session.commit()
        await self.user_repo.session.refresh(user)
        return user

    async def authenticate_user(self, email: str, password: str) -> Token:
        user = await self.user_repo.get_by_email(email)

        if not user or not security.verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = security.create_access_token(
            data={"sub": user.email}, expires_delta=access_token_expires
        )
        return Token(access_token=access_token, token_type="bearer")

    async def logout(self, token: str):
        try:
            payload = jwt.decode(
                token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
            )
            exp = payload.get("exp")

            if exp:
                current_timestamp = datetime.now(timezone.utc).timestamp()
                ttl = int(exp - current_timestamp)

                if ttl > 0:
                    await self.redis.set(f"blacklist:{token}", "true", ex=ttl)

        except jwt.PyJWTError:
            pass
