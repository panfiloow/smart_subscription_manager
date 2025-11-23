from typing import List
from fastapi import APIRouter, Depends, status

from app.api import deps
from app.schemas.subscription import (
    SubscriptionCreate,
    SubscriptionRead,
    SubscriptionUpdate,
)
from app.models.user import User
from app.schemas.subscription import AnalyticsResponse
from app.services.subscription_service import SubscriptionService

router = APIRouter()


@router.post("/", response_model=SubscriptionRead, status_code=status.HTTP_201_CREATED)
async def create_subscription(
    subscription_in: SubscriptionCreate,
    current_user: User = Depends(deps.get_current_user),
    service: SubscriptionService = Depends(deps.get_subscription_service),
):
    """
    Создать новую подписку.
    """
    return await service.create_subscription(
        user_id=current_user.id, sub_in=subscription_in
    )


@router.get("/", response_model=List[SubscriptionRead])
async def read_subscriptions(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_user),
    service: SubscriptionService = Depends(deps.get_subscription_service),
):
    """
    Получить список подписок текущего пользователя.
    """
    return await service.get_user_subscriptions(
        user_id=current_user.id, skip=skip, limit=limit
    )


@router.get("/analytics/monthly", response_model=AnalyticsResponse)
async def get_analytics(
    current_user: User = Depends(deps.get_current_user),
    service: SubscriptionService = Depends(deps.get_subscription_service),
):
    """
    Получить аналитику расходов (с кэшированием в Redis).
    """
    return await service.calculate_analytics(user_id=current_user.id)


@router.get("/{subscription_id}", response_model=SubscriptionRead)
async def read_subscription(
    subscription_id: int,
    current_user: User = Depends(deps.get_current_user),
    service: SubscriptionService = Depends(deps.get_subscription_service),
):
    """
    Получить конкретную подписку по ID (с проверкой владельца).
    """
    return await service.get_subscription(
        sub_id=subscription_id, user_id=current_user.id
    )


@router.put("/{subscription_id}", response_model=SubscriptionRead)
async def update_subscription(
    subscription_id: int,
    subscription_in: SubscriptionUpdate,
    current_user: User = Depends(deps.get_current_user),
    service: SubscriptionService = Depends(deps.get_subscription_service),
):
    """
    Обновить подписку.
    """
    return await service.update_subscription(
        sub_id=subscription_id, user_id=current_user.id, sub_in=subscription_in
    )


@router.delete("/{subscription_id}", response_model=SubscriptionRead)
async def delete_subscription(
    subscription_id: int,
    current_user: User = Depends(deps.get_current_user),
    service: SubscriptionService = Depends(deps.get_subscription_service),
):
    """
    Удалить подписку.
    """
    return await service.delete_subscription(
        sub_id=subscription_id, user_id=current_user.id
    )
