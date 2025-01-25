import json
import logging
from contextlib import asynccontextmanager
from os import environ

import redis
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app.model import Handler

logging.basicConfig(
    level=logging.INFO,  # Set the minimum logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",  # Log format
)
logger = logging.getLogger(__name__)


class TextInput(BaseModel):
    text: str


class EmbeddingOutput(BaseModel):
    embedding: list[float]
    description: str | None = None


class SimilarityOutput(BaseModel):
    similarity: float
    description: str | None = None


class Redis:
    def __init__(self):
        self.client = redis.Redis(
            host=environ.get("REDIS_HOST"),
            port=environ.get("REDIS_PORT"),
            decode_responses=True,
        )  # Directly return responses in non-binary
        logger.info(
            f"Redis database connection established for {environ.get("REDIS_HOST")} on port {environ.get("REDIS_PORT")}"
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


redis_object = None

@asynccontextmanager  # Makes sure redis connection is closed after application shutdown
async def lifespan(app: FastAPI):
    global redis_object
    redis_object = Redis()
    yield


# TODO: what to do when there is no Redis database?

handler = Handler()

app = FastAPI(lifespan=lifespan)


@app.post("/embed")
async def embed_text(text_input: TextInput) -> EmbeddingOutput:
    """
    Endpoint to creating embeddings from the input text.

    :param text_input: The text to embed.
    :return: The embedding of the input text as JSON.
    """
    logger.info(f"Embedding text: {text_input.text}")
    global redis_object
    logging.info(f"text_input.text: {text_input.text}")
    
    cached_embedding =  redis_object.get_key(text_input.text)
    logging.info(f"cached_embedding: {cached_embedding}")
    logging.info(f"type cached_embedding: {type(cached_embedding)}")
    if cached_embedding:
        return EmbeddingOutput(
            embedding=json.loads(cached_embedding),
            description="The list of float values representing the text embedding.",
        )
    else:
        try:
            embedding = handler.embed(text_input.text)
            redis_object.client.set(text_input.text, json.dumps(embedding))
            return EmbeddingOutput(
                embedding=embedding,
                description="The list of float values representing the text embedding.",
            )
        except RuntimeError:
            HTTPException(
                status_code=404,
                detail="Something went wrong with creating an embedding.",
            )


# @app.post("/similarity")
# async def calculate_similarity(
#     text_1: TextInput, text_2: TextInput
# ) -> SimilarityOutput:
#     """
#     Compute the cosine similarity between two input texts.

#     :param text_1: The first text.
#     :param text_2: The second text.
#     :return: The similarity score between the two input texts as JSON.
#     """
#     similarity_score = handler.similarity(text_1=text_1.text, text_2=text_2.text)
#     return SimilarityOutput(
#         similarity=similarity_score,
#         description="Cosine similarity indicating semantic similarity. A value close to 1.0 is very similar, close to 0.0 close to -1.0 means little to no similarity, is very dissimilar.",
#     )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="0.0.0.0", reload=True)
