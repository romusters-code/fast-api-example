import logging
from pinecone import Pinecone
from app.config.settings import Settings
from app.db.database_interface import DatabaseInterface
from typing import List

logging.basicConfig(
    level=logging.INFO,  # Set the minimum logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",  # Log format
)
logger = logging.getLogger(__name__)

settings = Settings()

class PineconeDatabase(DatabaseInterface):
    def __init__(self):
        self.DATABASE_URL = settings.DATABASE_URL
        self.PORT = settings.DATABASE_PORT
        self.API_KEY = settings.DATABASE_API_KEY
        self.client = None
    

    def connect(self):
        try:
            self.client = Pinecone(api_key=self.API_KEY, host=self.DATABASE_URL)
            logger.info("Pinecone initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize Pinecone: {e}")



    def get(self, key: str):
        """
        Retrieves a key from Redis if it exists.

        :param redis_url: Redis connection URL.
        :param key: The key to retrieve.
        :return: The value of the key if it exists, otherwise None.
        """
        index = self.client.Index(host=self.DATABASE_URL)
        # Check if the key exists
        fetch_response = index.fetch(key)
        if fetch_response:
            return fetch_response
        return None
    

    def set(self, key: str, value: List[float]):
        upsert_response = self.client.Index.upsert(vectors=[(key, value)])
        logging.info(f"The key {key[0:10]}... was upserted with response {upsert_response}")