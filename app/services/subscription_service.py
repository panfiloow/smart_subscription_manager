from decimal import Decimal
from typing import Sequence
import uuid

from fastapi import HTTPException
from redis.asyncio import Redis

from app.repositories.subscription_repository import SubscriptionRepository
from app.schemas.subscription import (
    SubscriptionCreate,
    SubscriptionUpdate,
    AnalyticsResponse,
    Currency,
)
from app.models.subscription import Subscription

EXCHANGE_RATES = {
    Currency.RUB: Decimal("1.0"),
    Currency.USD: Decimal("100.0"),
    Currency.EUR: Decimal("110.0"),
    Currency.KZT: Decimal("0.2"),
}


class SubscriptionService:
    def __init__(self, sub_repo: SubscriptionRepository, redis: Redis):
        self.repo = sub_repo
        self.redis = redis

    async def _clear_cache(self, user_id: uuid.UUID):
        """Приватный метод для сброса кэша аналитики"""
        await self.redis.delete(f"analytics:{user_id}")

    async def create_subscription(
        self, user_id: uuid.UUID, sub_in: SubscriptionCreate
    ) -> Subscription:
        sub = await self.repo.create(sub_in, user_id)

        await self.repo.session.commit()
        await self.repo.session.refresh(sub)

        await self._clear_cache(user_id)

        return sub

    async def get_user_subscriptions(
        self, user_id: uuid.UUID, skip: int = 0, limit: int = 100
    ) -> Sequence[Subscription]:
        return await self.repo.get_multi_by_owner(user_id, skip, limit)

    async def get_subscription(self, sub_id: int, user_id: uuid.UUID) -> Subscription:
        sub = await self.repo.get(sub_id)

        if not sub:
            raise HTTPException(status_code=404, detail="Subscription not found")

        if sub.user_id != user_id:
            raise HTTPException(status_code=404, detail="Subscription not found")

        return sub

    async def update_subscription(
        self, sub_id: int, user_id: uuid.UUID, sub_in: SubscriptionUpdate
    ) -> Subscription:
        sub = await self.get_subscription(sub_id, user_id)

        updated_sub = await self.repo.update(sub, sub_in)

        await self.repo.session.commit()
        await self.repo.session.refresh(updated_sub)

        await self._clear_cache(user_id)

        return updated_sub

    async def delete_subscription(
        self, sub_id: int, user_id: uuid.UUID
    ) -> Subscription:
        sub = await self.get_subscription(sub_id, user_id)

        await self.repo.delete(sub)
        await self.repo.session.commit()

        await self._clear_cache(user_id)
        return sub

    async def calculate_analytics(self, user_id: uuid.UUID) -> AnalyticsResponse:
        cache_key = f"analytics:{user_id}"

        cached_data = await self.redis.get(cache_key)
        if cached_data:
            return AnalyticsResponse.model_validate_json(cached_data)

        raw_totals = await self.repo.get_total_cost_by_currency(user_id)

        final_total_rub = Decimal("0.0")
        details = {}

        for currency_str, total_amount in raw_totals:
            amount = total_amount if total_amount else Decimal("0.0")
            try:
                currency_enum = Currency(currency_str)
            except ValueError:
                currency_enum = Currency.RUB

            details[currency_enum] = amount
            rate = EXCHANGE_RATES.get(currency_enum, Decimal("1.0"))
            final_total_rub += amount * rate

        response = AnalyticsResponse(
            total_monthly_price=final_total_rub.quantize(Decimal("1.00")),
            details=details,
        )

        await self.redis.set(cache_key, response.model_dump_json(), ex=600)

        return response
