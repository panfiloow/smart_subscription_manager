import pytest
from unittest.mock import AsyncMock, MagicMock
from decimal import Decimal
import uuid
import json

from app.services.subscription_service import SubscriptionService
from app.core.exceptions import SubscriptionNotFoundException
from app.schemas.subscription import  SubscriptionCreate, SubscriptionUpdate

@pytest.fixture
def mock_sub_repo():
    return AsyncMock()

@pytest.fixture
def mock_redis():
    return AsyncMock()

@pytest.fixture
def sub_service(mock_sub_repo, mock_redis):
    return SubscriptionService(sub_repo=mock_sub_repo, redis=mock_redis)

@pytest.mark.asyncio
async def test_create_subscription(sub_service, mock_sub_repo, mock_redis):
    user_id = uuid.uuid4()
    sub_in = SubscriptionCreate(name="Test", price=10, currency="USD", payment_date=1)
    
    await sub_service.create_subscription(user_id, sub_in)
    
    mock_sub_repo.create.assert_awaited_once()
    mock_sub_repo.session.commit.assert_awaited_once()
    mock_redis.delete.assert_awaited_with(f"analytics:{user_id}")

@pytest.mark.asyncio
async def test_get_subscription_success(sub_service, mock_sub_repo):
    user_id = uuid.uuid4()
    mock_sub = MagicMock()
    mock_sub.user_id = user_id
    mock_sub_repo.get.return_value = mock_sub
    
    result = await sub_service.get_subscription(1, user_id)
    assert result == mock_sub

@pytest.mark.asyncio
async def test_get_subscription_not_found(sub_service, mock_sub_repo):
    mock_sub_repo.get.return_value = None
    
    with pytest.raises(SubscriptionNotFoundException):
        await sub_service.get_subscription(1, uuid.uuid4())

@pytest.mark.asyncio
async def test_get_subscription_wrong_owner(sub_service, mock_sub_repo):
    owner_id = uuid.uuid4()
    hacker_id = uuid.uuid4()
    
    mock_sub = MagicMock()
    mock_sub.user_id = owner_id
    mock_sub_repo.get.return_value = mock_sub
    
    with pytest.raises(SubscriptionNotFoundException):
        await sub_service.get_subscription(1, hacker_id)

@pytest.mark.asyncio
async def test_update_subscription(sub_service, mock_sub_repo, mock_redis):
    user_id = uuid.uuid4()
    mock_sub = MagicMock()
    mock_sub.user_id = user_id
    mock_sub_repo.get.return_value = mock_sub
    
    sub_update = SubscriptionUpdate(name="New Name")
    
    await sub_service.update_subscription(1, user_id, sub_update)
    
    mock_sub_repo.update.assert_awaited_once()
    mock_sub_repo.session.commit.assert_awaited_once()
    mock_redis.delete.assert_awaited_with(f"analytics:{user_id}")

@pytest.mark.asyncio
async def test_analytics_cache_hit(sub_service, mock_redis, mock_sub_repo):
    user_id = uuid.uuid4()
    cached_json = json.dumps({
        "total_monthly_price": "100.00",
        "details": {"RUB": "100.00"}
    })
    mock_redis.get.return_value = cached_json
    
    result = await sub_service.calculate_analytics(user_id)
    
    assert result.total_monthly_price == Decimal("100.00")
    mock_sub_repo.get_total_cost_by_currency.assert_not_awaited()

@pytest.mark.asyncio
async def test_analytics_cache_miss_logic(sub_service, mock_redis, mock_sub_repo):
    user_id = uuid.uuid4()
    mock_redis.get.return_value = None
    
    mock_sub_repo.get_total_cost_by_currency.return_value = [
        ("USD", Decimal("10.00")),
        ("RUB", Decimal("100.00")),
        ("BAD_CURRENCY", Decimal("50.00")) 
    ]
    
    result = await sub_service.calculate_analytics(user_id)
    
    expected = Decimal("1150.00")
    assert result.total_monthly_price == expected
    
    mock_redis.set.assert_awaited_once()

@pytest.mark.asyncio
async def test_analytics_redis_failure(sub_service, mock_redis, mock_sub_repo):
    """
    Тестируем сценарий, когда Redis упал (вызывает Exception).
    Приложение НЕ должно упасть, оно должно посчитать через БД.
    """
    user_id = uuid.uuid4()
    
    mock_redis.get.side_effect = Exception("Redis Connection Error")
    
    mock_redis.set.side_effect = Exception("Redis Write Error")
    
    mock_sub_repo.get_total_cost_by_currency.return_value = [("RUB", Decimal("100"))]
    
    result = await sub_service.calculate_analytics(user_id)
    
    assert result.total_monthly_price == Decimal("100.00")