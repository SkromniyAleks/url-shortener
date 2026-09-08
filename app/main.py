from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import Base, engine
from app.redis_client import close_redis
from app.routers import links, redirect


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Создаём таблицы при старте, очищаем ресурсы при завершении."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await close_redis()
    await engine.dispose()


app = FastAPI(
    title="URL Shortener API",
    description="Высоконагруженный сервис сокращения ссылок с аналитикой",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health", tags=["system"])
async def health():
    """Проверка работоспособности."""
    return {"status": "ok"}


# ВАЖНО: API-роуты регистрируем ДО catch-all редиректа
app.include_router(links.router)
app.include_router(redirect.router)