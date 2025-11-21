from typing import Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.subscription import Subscription
from app.schemas.subscription import SubscriptionCreate, SubscriptionUpdate
import uuid


class CRUDSubscription:
    async def create(
        self, db: AsyncSession, obj_in: SubscriptionCreate, user_id: uuid.UUID
    ) -> Subscription:
        db_obj = Subscription(**obj_in.model_dump(), user_id=user_id)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get_multi_by_owner(
        self, db: AsyncSession, user_id: uuid.UUID, skip: int = 0, limit: int = 100
    ) -> Sequence[Subscription]:
        """Получить список подписок конкретного пользователя"""
        query = (
            select(Subscription)
            .where(Subscription.user_id == user_id)
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(query)
        return result.scalars().all()

    async def get(self, db: AsyncSession, id: int) -> Subscription | None:
        query = select(Subscription).where(Subscription.id == id)
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    async def update(
        self, 
        db: AsyncSession, 
        *, 
        db_obj: Subscription, 
        obj_in: SubscriptionUpdate | dict
    ) -> Subscription:
        """
        Обновление полей подписки.
        Принимает объект из БД (db_obj) и новые данные (obj_in).
        """
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)

        for field in update_data:
            if hasattr(db_obj, field):
                setattr(db_obj, field, update_data[field])

        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    
    async def remove(self, db: AsyncSession, *, id: int) -> Subscription:
        """Удаление подписки по ID"""
        query = select(Subscription).where(Subscription.id == id)
        result = await db.execute(query)
        obj = result.scalar_one_or_none()
        
        if obj:
            await db.delete(obj)
            await db.commit()
        return obj

subscription = CRUDSubscription()
