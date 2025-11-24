import pytest
from httpx import AsyncClient
from redis.asyncio import Redis

async def get_auth_headers(client: AsyncClient, email: str):
    pwd = "password"
    await client.post("/api/v1/auth/register", json={"email": email, "password": pwd})
    resp = await client.post("/api/v1/auth/login", data={"username": email, "password": pwd})
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.mark.asyncio
async def test_analytics_calculation(client: AsyncClient):
    headers = await get_auth_headers(client, "analytics@test.com")
    await client.post("/api/v1/subscriptions/", json={"name": "S1", "price": 10, "currency": "USD", "payment_date": 1}, headers=headers)
    await client.post("/api/v1/subscriptions/", json={"name": "S2", "price": 500, "currency": "RUB", "payment_date": 1}, headers=headers)
    
    response = await client.get("/api/v1/subscriptions/analytics/monthly", headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["total_monthly_price"] == "1500.00"
    assert data["details"]["USD"] == "10.00"
    assert data["details"]["RUB"] == "500.00"

@pytest.mark.asyncio
async def test_analytics_redis_cache_invalidation(client: AsyncClient, redis_client: Redis):
    """
    Проверяем, что кэш создается при запросе и удаляется при обновлении данных.
    """
    email = "cache@test.com"
    pwd = "pass"
    await client.post("/api/v1/auth/register", json={"email": email, "password": pwd})
    login_resp = await client.post("/api/v1/auth/login", data={"username": email, "password": pwd})
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    sub_resp = await client.post("/api/v1/subscriptions/", json={"name": "S1", "price": 100, "currency": "RUB", "payment_date": 1}, headers=headers)
    sub_id = sub_resp.json()["id"]

    await client.get("/api/v1/subscriptions/analytics/monthly", headers=headers)
    
    keys = await redis_client.keys("analytics:*")
    assert len(keys) == 1
    
    await client.put(f"/api/v1/subscriptions/{sub_id}", json={"price": 200}, headers=headers)
    
    keys_after_update = await redis_client.keys("analytics:*")
    assert len(keys_after_update) == 0
    
    resp_new = await client.get("/api/v1/subscriptions/analytics/monthly", headers=headers)
    assert resp_new.json()["total_monthly_price"] == "200.00"
    
    keys_final = await redis_client.keys("analytics:*")
    assert len(keys_final) == 1