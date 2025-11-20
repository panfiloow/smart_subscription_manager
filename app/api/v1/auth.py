from datetime import timedelta
from typing import Annotated
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from app.schemas.user import UserCreate, UserRead
from app.api.deps import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.core.security import get_password_hash, verify_password, create_access_token, oauth2_scheme
from app.schemas.token import Token
from app.core.config import settings


auth_router = APIRouter(prefix="/v1/auth", tags=["Auth"])


@auth_router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    responses={409: {"description": "Email already registered"}},
)
async def register_user(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    result_email = await db.execute(select(User).where(User.email == user_data.email))
    existing_user = result_email.scalar_one_or_none()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email already registered"
        )

    hashed_password = get_password_hash(user_data.password)
    new_user = User(email=user_data.email, hashed_password=hashed_password)
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user

@auth_router.post("/login", response_model=Token)
async def login_user(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()], 
    db: AsyncSession = Depends(get_db)
):
    # 1. Ищем пользователя
    # ВАЖНО: form_data.username содержит email, который ввел пользователь!
    query = select(User).where(User.email == form_data.username)
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    # 2. Проверяем пароль и наличие юзера
    # Объединяем проверки, чтобы возвращать одну и ту же ошибку
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 3. Создаем токен
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Передаем словарь (как ты и писал в create_access_token)
    # "sub" (subject) - стандартное поле JWT для идентификатора пользователя
    access_token = create_access_token(
        data={"sub": user.email}, 
        expires_delta=access_token_expires
    )
    
    return Token(access_token=access_token, token_type="bearer")

@auth_router.get("/test_token")
async def test_token(token: str = Depends(oauth2_scheme)):
    # oauth2_scheme проверит наличие заголовка Authorization
    # Если токена нет - вернет 401 ошибку
    # Если токен есть - положит его в переменную token
    return {"your_token": token}