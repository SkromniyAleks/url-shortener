import redis.asyncio as redis

from app.config import settings

redis_client = redis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)


async def get_cached_url(short_code: str) -> str | None:
    """Получить URL из кэша."""
    return await redis_client.get(f"url:{short_code}")


async def set_cached_url(short_code: str, url: str, ttl: int = settings.CACHE_TTL) -> None:
    """Записать URL в кэш с TTL."""
    await redis_client.set(f"url:{short_code}", url, ex=ttl)


async def close_redis() -> None:
    """Закрыть соединение с Redis."""
    await redis_client.aclose()