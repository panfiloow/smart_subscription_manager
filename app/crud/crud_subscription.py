from typing import Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.subscription import Subscription
from app.schemas.subscription import SubscriptionCreate
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

subscription = CRUDSubscription()
