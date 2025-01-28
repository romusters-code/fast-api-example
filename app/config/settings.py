import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = os.getenv("DATABASE_HOST", "dummy")
    DATABASE_PORT: str = os.getenv("DATABASE_PORT", "dummy")
    DATABASE_KIND: str = os.getenv("DATABASE_KIND", "dummy")
    DATABASE_API_KEY: str = os.getenv("DATABASE_API_KEY", "dummy-api-key")
    CACHE_ENABLED: bool = os.getenv("CACHE_ENABLED", "dummy")

settings = Settings()