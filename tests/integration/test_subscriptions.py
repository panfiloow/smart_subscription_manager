import pytest
from httpx import AsyncClient

# Хелпер для быстрой авторизации в тестах
async def get_auth_headers(client: AsyncClient, email: str):
    pwd = "password"
    await client.post("/api/v1/auth/register", json={"email": email, "password": pwd})
    resp = await client.post("/api/v1/auth/login", data={"username": email, "password": pwd})
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.mark.asyncio
async def test_create_subscription(client: AsyncClient):
    headers = await get_auth_headers(client, "sub_create@test.com")
    payload = {
        "name": "Netflix",
        "price": 12.99,
        "currency": "USD",
        "payment_date": 15
    }
    response = await client.post("/api/v1/subscriptions/", json=payload, headers=headers)
    
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Netflix"
    assert data["currency"] == "USD"
    assert data["id"] is not None

@pytest.mark.asyncio
async def test_create_subscription_invalid_date(client: AsyncClient):
    headers = await get_auth_headers(client, "sub_invalid@test.com")
    payload = {
        "name": "Netflix",
        "price": 10,
        "currency": "RUB",
        "payment_date": 35 
    }
    response = await client.post("/api/v1/subscriptions/", json=payload, headers=headers)
    assert response.status_code == 422 

@pytest.mark.asyncio
async def test_get_subscriptions_list(client: AsyncClient):
    headers = await get_auth_headers(client, "sub_list@test.com")
    await client.post("/api/v1/subscriptions/", json={"name": "A2", "price": 10, "currency": "RUB", "payment_date": 1}, headers=headers)
    await client.post("/api/v1/subscriptions/", json={"name": "B2", "price": 20, "currency": "RUB", "payment_date": 1}, headers=headers)
    
    response = await client.get("/api/v1/subscriptions/", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2

@pytest.mark.asyncio
async def test_update_subscription(client: AsyncClient):
    headers = await get_auth_headers(client, "sub_update@test.com")
    create_resp = await client.post("/api/v1/subscriptions/", json={"name": "Old", "price": 10, "currency": "RUB", "payment_date": 1}, headers=headers)
    sub_id = create_resp.json()["id"]
    
    update_payload = {"name": "New Name", "price": 150}
    response = await client.put(f"/api/v1/subscriptions/{sub_id}", json=update_payload, headers=headers)
    
    assert response.status_code == 200
    assert response.json()["name"] == "New Name"
    assert response.json()["price"] == "150.00"

@pytest.mark.asyncio
async def test_delete_subscription(client: AsyncClient):
    headers = await get_auth_headers(client, "sub_del@test.com")
    create_resp = await client.post("/api/v1/subscriptions/", json={"name": "Del", "price": 10, "currency": "RUB", "payment_date": 1}, headers=headers)
    sub_id = create_resp.json()["id"]
    
    del_resp = await client.delete(f"/api/v1/subscriptions/{sub_id}", headers=headers)
    assert del_resp.status_code == 200
    
    get_resp = await client.get(f"/api/v1/subscriptions/{sub_id}", headers=headers)
    assert get_resp.status_code == 404

@pytest.mark.asyncio
async def test_idor_protection_access_denied(client: AsyncClient):
    """
    Тест защиты IDOR:
    User B не должен иметь возможности удалить или прочитать подписку User A.
    """
    headers_a = await get_auth_headers(client, "user_a@test.com")
    resp_a = await client.post("/api/v1/subscriptions/", json={"name": "Secret", "price": 10, "currency": "RUB", "payment_date": 1}, headers=headers_a)
    sub_id_a = resp_a.json()["id"]
    
    headers_b = await get_auth_headers(client, "user_b@test.com")
    
    resp_delete = await client.delete(f"/api/v1/subscriptions/{sub_id_a}", headers=headers_b)
    assert resp_delete.status_code == 404 
    
    resp_get = await client.get(f"/api/v1/subscriptions/{sub_id_a}", headers=headers_b)
    assert resp_get.status_code == 404