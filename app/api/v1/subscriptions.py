from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.crud import crud_subscription
from app.schemas.subscription import SubscriptionCreate, SubscriptionRead, SubscriptionUpdate
from app.models.user import User

router = APIRouter()


@router.post("/", response_model=SubscriptionRead, status_code=status.HTTP_201_CREATED)
async def create_subscription(
    subscription_in: SubscriptionCreate,
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db),
):
    return await crud_subscription.subscription.create(
        db=db, obj_in=subscription_in, user_id=current_user.id
    )


@router.get("/", response_model=List[SubscriptionRead])
async def read_subscriptions(
    db: AsyncSession = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_user),
):
    return await crud_subscription.subscription.get_multi_by_owner(
        db=db, user_id=current_user.id, skip=skip, limit=limit
    )

@router.get("/{subscription_id}", response_model=SubscriptionRead)
async def read_subscription(
    subscription_id: int,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """
    Получить конкретную подписку по ID.
    """
    subscription = await crud_subscription.subscription.get(db, id=subscription_id)
    
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")
    
    if subscription.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Subscription not found")
        
    return subscription

@router.put("/{subscription_id}", response_model=SubscriptionRead)
async def update_subscription(
    subscription_id: int,
    subscription_in: SubscriptionUpdate,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """
    Обновить подписку.
    """
    subscription = await crud_subscription.subscription.get(db, id=subscription_id)
    
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")
    
    if subscription.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Subscription not found")

    subscription = await crud_subscription.subscription.update(
        db, db_obj=subscription, obj_in=subscription_in
    )
    return subscription

@router.delete("/{subscription_id}", response_model=SubscriptionRead)
async def delete_subscription(
    subscription_id: int,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """
    Удалить подписку.
    """
    subscription = await crud_subscription.subscription.get(db, id=subscription_id)
    
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")
    
    if subscription.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Subscription not found")

    await crud_subscription.subscription.remove(db, id=subscription_id)
    return subscription