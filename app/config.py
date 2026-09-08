from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://user:pass@localhost:5432/shortener"
    REDIS_URL: str = "redis://localhost:6379/0"
    SHORT_CODE_LENGTH: int = 6
    CACHE_TTL: int = 3600  # 1 час
    BASE_URL: str = "http://localhost"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()