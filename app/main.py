from contextlib import asynccontextmanager
from fastapi import FastAPI
from sqlalchemy import text
from app.db.session import engine
from app.api.v1 import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        print("✅ Connection to PostgreSQL successful!")
    except Exception as e:
        print(f"❌ Connection failed: {e}")

    yield

    await engine.dispose()


app = FastAPI(lifespan=lifespan)
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
def read_root():
    return {"message": "Subscription Manager API is running"}
