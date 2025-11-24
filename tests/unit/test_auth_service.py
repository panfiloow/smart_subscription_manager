import jwt
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.auth_service import AuthService
from app.schemas.user import UserCreate
from app.core.exceptions import UserAlreadyExistsException, InvalidCredentialsException

EMAIL = "test@example.com"
PASSWORD = "password"
HASHED_PASSWORD = "hashed_password"

@pytest.fixture
def mock_user_repo():
    return AsyncMock()

@pytest.fixture
def mock_redis():
    return AsyncMock()

@pytest.fixture
def auth_service(mock_user_repo, mock_redis):
    return AuthService(user_repo=mock_user_repo, redis=mock_redis)

@pytest.mark.asyncio
async def test_register_user_success(auth_service, mock_user_repo):
    mock_user_repo.get_by_email.return_value = None
    
    with patch("app.core.security.get_password_hash", return_value=HASHED_PASSWORD):
        user_in = UserCreate(email=EMAIL, password=PASSWORD)
        await auth_service.register_user(user_in)
    
    mock_user_repo.get_by_email.assert_awaited_once_with(EMAIL)
    mock_user_repo.create.assert_awaited_once()
    mock_user_repo.session.commit.assert_awaited_once()

@pytest.mark.asyncio
async def test_register_user_duplicate(auth_service, mock_user_repo):
    mock_user_repo.get_by_email.return_value = MagicMock() 
    
    user_in = UserCreate(email=EMAIL, password=PASSWORD)
    
    with pytest.raises(UserAlreadyExistsException):
        await auth_service.register_user(user_in)
    
    mock_user_repo.create.assert_not_awaited()

@pytest.mark.asyncio
async def test_authenticate_user_success(auth_service, mock_user_repo):
    mock_user = MagicMock()
    mock_user.email = EMAIL
    mock_user.hashed_password = HASHED_PASSWORD
    mock_user_repo.get_by_email.return_value = mock_user
    
    with patch("app.core.security.verify_password", return_value=True):
        with patch("app.core.security.create_access_token", return_value="token"):
            token = await auth_service.authenticate_user(EMAIL, PASSWORD)
    
    assert token.access_token == "token"

@pytest.mark.asyncio
async def test_authenticate_user_not_found(auth_service, mock_user_repo):
    mock_user_repo.get_by_email.return_value = None
    
    with pytest.raises(InvalidCredentialsException):
        await auth_service.authenticate_user(EMAIL, PASSWORD)

@pytest.mark.asyncio
async def test_authenticate_user_wrong_password(auth_service, mock_user_repo):
    mock_user = MagicMock()
    mock_user.hashed_password = HASHED_PASSWORD
    mock_user_repo.get_by_email.return_value = mock_user
    
    with patch("app.core.security.verify_password", return_value=False):
        with pytest.raises(InvalidCredentialsException):
            await auth_service.authenticate_user(EMAIL, PASSWORD)

@pytest.mark.asyncio
async def test_logout_success(auth_service, mock_redis):
    token = "valid_token"
    mock_payload = {"exp": 1234567890}
    
    with patch("jwt.decode", return_value=mock_payload):
        with patch("app.services.auth_service.datetime") as mock_datetime:
            mock_datetime.now.return_value.timestamp.return_value = 1234560000 
            mock_datetime.timezone = MagicMock() 
            
            await auth_service.logout(token)
            
    mock_redis.set.assert_awaited_once()

@pytest.mark.asyncio
async def test_logout_invalid_token(auth_service, mock_redis):
    with patch("jwt.decode", side_effect=jwt.PyJWTError("Invalid token")):
        await auth_service.logout("bad_token")
    
    mock_redis.set.assert_not_awaited()