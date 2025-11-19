from contextlib import asynccontextmanager
from fastapi import FastAPI
from sqlalchemy import text
from app.db.session import engine

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Код, который выполняется при старте приложения
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        print("✅ Connection to PostgreSQL successful!")
    except Exception as e:
        print(f"❌ Connection failed: {e}")
    
    yield
    
    # Код, который выполняется при выключении (если нужно закрыть пул)
    await engine.dispose()


app = FastAPI(lifespan=lifespan)

@app.get("/")
def read_root():
    return {"message": "Subscription Manager API is running"}