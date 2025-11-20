from typing import Optional
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User
from app.schemas.user import UserCreate
from app.core.security import get_password_hash

class CRUDUser:
    
    async def get_by_email(self, db: AsyncSession, email: str) -> Optional[User]:
        """Найти пользователя по email"""
        query = select(User).where(User.email == email)
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    async def get(self, db: AsyncSession, id: uuid.UUID) -> Optional[User]:
        """Найти пользователя по ID"""
        query = select(User).where(User.id == id)
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    async def create(self, db: AsyncSession, obj_in: UserCreate) -> User:
        """Создать нового пользователя"""
        db_obj = User(
            email=obj_in.email,
            hashed_password=get_password_hash(obj_in.password)
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

user = CRUDUser()