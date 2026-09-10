from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # База и кэш: пусто/sqlite = демо-режим, в Docker значения приходят из .env
    DATABASE_URL: str = "sqlite+aiosqlite:///./shortener_demo.db"
    REDIS_URL: str = ""
    BASE_URL: str = "http://localhost"
    SHORT_CODE_LENGTH: int = 6
    CACHE_TTL: int = 3600

    # Auth (Фаза 1)
    SECRET_KEY: str = "dev-secret-change-me"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    ADMIN_USERNAME: str = "Alex"
    ADMIN_PASSWORD: str = "Alex123"

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()