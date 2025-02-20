import logging
from abc import ABC, abstractmethod

logging.basicConfig(
    level=logging.INFO,  # Set the minimum logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",  # Log format
)
logger = logging.getLogger(__name__)


class DatabaseInterface(ABC):
    @abstractmethod
    def connect(self):
        pass

    @abstractmethod
    def set(self, key, value):
        pass

    @abstractmethod
    def get(self, key):
        pass

    # TODO
    # @abstractmethod
    # def close(self):
    #     pass

    # def __enter__(self):
    #     # Opening the connection
    #     self.connect()
    #     return self

    # def __exit__(self, exc_type, exc_val, exc_tb):
    #     # Closing the connection, even on error
    #     self.close()
