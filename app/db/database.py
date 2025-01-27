import logging
import redis

from app.config.settings import Settings

logging.basicConfig(
    level=logging.INFO,  # Set the minimum logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",  # Log format
)
logger = logging.getLogger(__name__)

settings = Settings()

class Redis:
    # TODO: what to do when there is no Redis database?
    def __init__(self):
        self.client = redis.Redis(
            host=settings.DATABASE_URL,
            port=settings.DATABASE_PORT,
            decode_responses=True,
        )  # Directly return responses in non-binary
        logger.info(
            f"Redis database connection established for {settings.DATABASE_URL} on port {settings.DATABASE_PORT}"
        )

    def get_key(self, key: str):
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