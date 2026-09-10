from typing import AsyncGenerator
from unittest.mock import AsyncMock, patch

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base, get_db
from app.main import app
from app.services import user_service

# In-memory SQLite для тестов
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def override_get_db():
    """Переопределяем зависимость БД для тестов."""
    async with TestSessionLocal() as session:
        yield session


app.dependency_overrides[get_db] = override_get_db


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Фикстура: клиент с тестовой БД и заглушками кэша."""
    # Создаём таблицы перед тестом
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Сидим админа, чтобы админ-сценарии работали в тестах
    async with TestSessionLocal() as session:
        await user_service.ensure_admin(session)

    # Подменяем функции кэша на заглушки (чтобы не нужен реальный Redis)
    with patch("app.routers.redirect.get_cached_url", new_callable=AsyncMock, return_value=None), \
         patch("app.routers.redirect.set_cached_url", new_callable=AsyncMock), \
         patch("app.routers.links.delete_cached_url", new_callable=AsyncMock), \
         patch("app.routers.links.clear_cache", new_callable=AsyncMock):

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac

    # Удаляем таблицы после теста
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)