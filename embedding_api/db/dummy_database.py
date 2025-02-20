import logging
from typing import List

from embedding_api.config.settings import Settings
from embedding_api.db.database_interface import DatabaseInterface

logging.basicConfig(
    level=logging.INFO,  # Set the minimum logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",  # Log format
)
logger = logging.getLogger(__name__)

settings = Settings()


class DummyDatabase(DatabaseInterface):
    def __init__(self):
        return

    def connect(self):
        return

    def set(self, key: str, value: List[float]):
        return

    def get(self, key: str):
        return
