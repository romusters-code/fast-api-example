import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = os.getenv("DATABASE_HOST")
    DATABASE_PORT: str = os.getenv("DATABASE_PORT")
    DATABASE_KIND: str = os.getenv("DATABASE_KIND")
    DATABASE_API_KEY: str = os.getenv("DATABASE_API_KEY", "dummy-api-key")

settings = Settings()