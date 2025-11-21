from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.crud import crud_subscription
from app.schemas.subscription import SubscriptionCreate, SubscriptionRead
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
