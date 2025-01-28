import logging
import time

from app.config.settings import Settings
from app.db.database_interface import DatabaseInterface
from pinecone.grpc import PineconeGRPC as Pinecone
from typing import List


logging.basicConfig(
    level=logging.INFO,  # Set the minimum logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",  # Log format
)
logger = logging.getLogger(__name__)

settings = Settings()

class PineconeDatabase(DatabaseInterface):
    def __init__(self):
        self.DATABASE_URL = f"{settings.DATABASE_URL}:{settings.DATABASE_PORT}"
        self.PORT = settings.DATABASE_PORT
        self.API_KEY = settings.DATABASE_API_KEY
        self.client = None
        self.index_name = 'default'
    

    def connect(self):
        try:
            self.client = Pinecone(api_key=self.API_KEY, host=self.DATABASE_URL)
            logger.info(f"Pinecone api_key: {self.API_KEY}, host: {self.DATABASE_URL} .")
            logger.info("Pinecone initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize Pinecone: {e}")

    def check_index(self, index_name: str = 'default') -> None:
        
        if not self.client.has_index(index_name):  
            self.client.create_index(
                name=index_name,
                dimension=2,
                metric="cosine",
            )

        # Wait for the index to be ready
        while not self.client.describe_index(self.index_name).status['ready']:
            time.sleep(1)



    def get(self, key: str):
        """
        Retrieves a key from Redis if it exists.

        :param redis_url: Redis connection URL.
        :param key: The key to retrieve.
        :return: The value of the key if it exists, otherwise None.
        """
        self.check_index()
        index = self.client.Index(host=self.DATABASE_URL)
        # Check if the key exists
        fetch_response = index.fetch(key)
        if fetch_response:
            return fetch_response
        return None
    

    def set(self, key: str, value: List[float]):
        self.check_index()
        index = self.client.Index(host=self.DATABASE_URL)
        upsert_response = index.upsert(vectors=[(key, value)])
        logging.info(f"The key {key[0:10]}... was upserted with response {upsert_response}")