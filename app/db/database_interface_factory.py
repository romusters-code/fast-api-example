import logging

from app.db.redis_database import RedisDatabase
from app.db.pinecone_database import PineconeDatabase


logging.basicConfig(
    level=logging.INFO,  # Set the minimum logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",  # Log format
)
logger = logging.getLogger(__name__)

class DatabaseFactory:

    @staticmethod
    def get_database(db_type, **kwargs):
        if db_type == 'redis':
            return RedisDatabase(**kwargs)
        elif db_type == 'pinecone':
            return PineconeDatabase(**kwargs)
        else:
            raise ValueError(f"Unsupported database type: {db_type}")
