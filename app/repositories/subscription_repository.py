from typing import Optional, Sequence
import uuid
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.subscription import Subscription
from app.schemas.subscription import SubscriptionCreate, SubscriptionUpdate


class SubscriptionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self, obj_in: SubscriptionCreate, user_id: uuid.UUID
    ) -> Subscription:
        db_obj = Subscription(**obj_in.model_dump(), user_id=user_id)
        self.session.add(db_obj)
        await self.session.flush()
        return db_obj

    async def get(self, id: int) -> Optional[Subscription]:
        query = select(Subscription).where(Subscription.id == id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_multi_by_owner(
        self, user_id: uuid.UUID, skip: int = 0, limit: int = 100
    ) -> Sequence[Subscription]:
        query = (
            select(Subscription)
            .where(Subscription.user_id == user_id)
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return result.scalars().all()

    async def update(
        self, db_obj: Subscription, obj_in: SubscriptionUpdate
    ) -> Subscription:
        update_data = obj_in.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(db_obj, field, value)

        self.session.add(db_obj)
        await self.session.flush()
        return db_obj

    async def delete(self, db_obj: Subscription) -> None:
        await self.session.delete(db_obj)
        await self.session.flush()

    async def get_total_cost_by_currency(self, user_id: uuid.UUID):
        """Агрегация для аналитики"""
        query = (
            select(Subscription.currency, func.sum(Subscription.price))
            .where(Subscription.user_id == user_id)
            .where(Subscription.is_active)
            .group_by(Subscription.currency)
        )
        result = await self.session.execute(query)
        return result.all()
