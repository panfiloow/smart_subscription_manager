from fastapi import HTTPException, status

class BaseAppException(HTTPException):
    """Базовый класс для всех ошибок приложения"""
    pass

class UserAlreadyExistsException(BaseAppException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )
    

class InvalidCredentialsException(BaseAppException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

class TokenExpiredException(BaseAppException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

class SubscriptionNotFoundException(BaseAppException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found"
        )