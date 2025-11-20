from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy import select
from app.schemas.user import UserCreate, UserRead
from app.api.deps import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User

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

    hashed_password = user_data.password
    new_user = User(email=user_data.email, hashed_password=hashed_password)
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user
