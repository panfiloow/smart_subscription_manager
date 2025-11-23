from fastapi import Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from redis.exceptions import RedisError

async def db_exception_handler(request: Request, exc: SQLAlchemyError):
    """
    Ловит ошибки PostgreSQL (разрыв соединения, синтаксис SQL и т.д.)
    """
    print(f"❌ DATABASE ERROR: {exc}") 
    
    return JSONResponse(
        status_code=503,
        content={"detail": "Database is temporarily unavailable. Please try again later."},
    )

async def redis_exception_handler(request: Request, exc: RedisError):
    """
    Ловит критические ошибки Redis
    """
    print(f"❌ REDIS ERROR: {exc}")
    
    return JSONResponse(
        status_code=503,
        content={"detail": "Cache service is unavailable. Please try again later."},
    )

async def generic_exception_handler(request: Request, exc: Exception):
    """
    Ловит вообще всё, что мы не предусмотрели (например, деление на ноль)
    """
    print(f"❌ UNHANDLED ERROR: {exc}")
    
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error. Our engineers have been notified."},
    )