import redis.asyncio as redis

from app.config import settings

_redis_client = (
    redis.from_url(settings.REDIS_URL, decode_responses=True)
    if settings.REDIS_URL
    else None
)

# Демо-режим: без Redis кэш живёт в обычной памяти процесса
_memory_cache: dict[str, str] = {}


async def get_cached_url(short_code: str) -> str | None:
    if _redis_client is None:
        return _memory_cache.get(short_code)
    value = await _redis_client.get(f"link:{short_code}")
    if value is None:
        return None
    return value.decode() if isinstance(value, bytes) else value


async def set_cached_url(short_code: str, url: str) -> None:
    if _redis_client is None:
        _memory_cache[short_code] = url
        return
    await _redis_client.set(f"link:{short_code}", url, ex=settings.CACHE_TTL)


async def delete_cached_url(short_code: str) -> None:
    """Инвалидация кэша одной ссылки (при удалении)."""
    if _redis_client is None:
        _memory_cache.pop(short_code, None)
        return
    await _redis_client.delete(f"link:{short_code}")


async def clear_cache() -> None:
    """Полная очистка кэша ссылок (при очистке БД)."""
    if _redis_client is None:
        _memory_cache.clear()
        return
    keys = [key async for key in _redis_client.scan_iter("link:*")]
    if keys:
        await _redis_client.delete(*keys)