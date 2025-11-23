import time
from fastapi import FastAPI, Request
from redis import RedisError
from app.core.exception_handlers import (
    db_exception_handler,
    generic_exception_handler,
    redis_exception_handler,
)
from app.api.v1 import api_router
from sqlalchemy.exc import SQLAlchemyError


app = FastAPI()
app.include_router(api_router, prefix="/api/v1")
app.add_exception_handler(SQLAlchemyError, db_exception_handler)
app.add_exception_handler(RedisError, redis_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)
app.add_exception_handler(OSError, db_exception_handler) 


# Время выполнения запроса
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()

    response = await call_next(request)

    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)

    return response

# Приветствие
@app.get("/")
def read_root():
    return {"message": "Subscription Manager API is running"}
