import logging
from typing import List

import redis

from app.config.settings import Settings
from app.db.database_interface import DatabaseInterface

logging.basicConfig(
    level=logging.INFO,  # Set the minimum logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",  # Log format
)
logger = logging.getLogger(__name__)

settings = Settings()


class RedisDatabase(DatabaseInterface):
    def __init__(self):
        self.host = settings.DATABASE_URL
        self.port = settings.DATABASE_PORT
        self.client = None

    def connect(self):
        self.client = redis.Redis(
            host=self.host,
            port=self.port,
            decode_responses=True,
        )  # Directly return responses in non-binary
        if not self.client.ping():
            raise ConnectionError("Could not connect to Redis!")
        else:
            logger.info(
                f"Redis database connection established for {settings.DATABASE_URL} on port {settings.DATABASE_PORT}"
            )
        return super().connect()

    def set(self, key: str, value: List[float]):
        self.client.set(key=key, value=value)

    def get(self, key: str):
        """
        Retrieves a key from Redis if it exists.

        :param redis_url: Redis connection URL.
        :param key: The key to retrieve.
        :return: The value of the key if it exists, otherwise None.
        """
        # Check if the key exists
        exists = self.client.exists(key)
        if exists:
            # Retrieve the key's value
            value = self.client.get(key)
            return value
        return None
