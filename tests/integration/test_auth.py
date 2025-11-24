import pytest
from httpx import AsyncClient
from redis.asyncio import Redis

EMAIL = "test_auth@example.com"
PASSWORD = "strongpassword123"

@pytest.mark.asyncio
async def test_register_user(client: AsyncClient):
    """Тест успешной регистрации"""
    payload = {"email": EMAIL, "password": PASSWORD}
    response = await client.post("/api/v1/auth/register", json=payload)
    
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == EMAIL
    assert "id" in data
    assert "hashed_password" not in data 

@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient):
    """Тест ошибки при регистрации существующего email"""
    payload = {"email": "duplicate@example.com", "password": PASSWORD}
    
    await client.post("/api/v1/auth/register", json=payload)
    
    response = await client.post("/api/v1/auth/register", json=payload)
    
    assert response.status_code == 409
    assert response.json()["detail"] == "Email already registered"

@pytest.mark.asyncio
async def test_login_flow(client: AsyncClient):
    """Тест логина и получения токена"""
    email = "login@example.com"
    await client.post("/api/v1/auth/register", json={"email": email, "password": PASSWORD})
    
    login_data = {"username": email, "password": PASSWORD}
    response = await client.post("/api/v1/auth/login", data=login_data)
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    
    return data["access_token"]

@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    """Тест логина с неверным паролем"""
    email = "wrong_pass@example.com"
    await client.post("/api/v1/auth/register", json={"email": email, "password": PASSWORD})
    
    response = await client.post("/api/v1/auth/login", data={"username": email, "password": "WRONG"})
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_get_current_user(client: AsyncClient):
    """Тест получения профиля (/users/me)"""
    email = "me@example.com"
    await client.post("/api/v1/auth/register", json={"email": email, "password": PASSWORD})
    resp = await client.post("/api/v1/auth/login", data={"username": email, "password": PASSWORD})
    token = resp.json()["access_token"]
    
    headers = {"Authorization": f"Bearer {token}"}
    response = await client.get("/api/v1/users/me", headers=headers)
    
    assert response.status_code == 200
    assert response.json()["email"] == email

@pytest.mark.asyncio
async def test_logout_and_blacklist(client: AsyncClient, redis_client: Redis):
    """Тест выхода и проверки Blacklist в Redis"""
    email = "logout@example.com"
    await client.post("/api/v1/auth/register", json={"email": email, "password": PASSWORD})
    resp = await client.post("/api/v1/auth/login", data={"username": email, "password": PASSWORD})
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    response = await client.post("/api/v1/auth/logout", headers=headers)
    assert response.status_code == 200
    
    in_blacklist = await redis_client.get(f"blacklist:{token}")
    assert in_blacklist is not None
    
    resp_me = await client.get("/api/v1/users/me", headers=headers)
    assert resp_me.status_code == 401 
    
    resp_logout_2 = await client.post("/api/v1/auth/logout", headers=headers)
    assert resp_logout_2.status_code == 401