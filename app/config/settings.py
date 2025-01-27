import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = os.getenv("REDIS_HOST")
    DATABASE_PORT: str = os.getenv("REDIS_PORT")


settings = Settings()