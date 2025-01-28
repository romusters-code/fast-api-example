import json
import logging

from app.config.settings import Settings
from app.db.database_interface_factory import DatabaseFactory
from app.model import Handler
from app.schemas.default import TextInput, EmbeddingOutput, SimilarityOutput
from fastapi import HTTPException
from fastapi import APIRouter


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

embed_router = APIRouter()

settings = Settings()

if settings.CACHE_ENABLED:
    database_object = DatabaseFactory.get_database(settings.DATABASE_KIND) # Switch between databases easily using an interface.
    database_object.connect()

handler = Handler()


@embed_router.post("/embed")
async def embed_text(text_input: TextInput) -> EmbeddingOutput:
    """
    Endpoint to creating embeddings from the input text.

    :param text_input: The text to embed.
    :return: The embedding of the input text as JSON.
    """
    logger.info(f"Embedding text: {text_input.text}")
    if settings.CACHE_ENABLED:
        cached_embedding =  database_object.get(text_input.text)
        if cached_embedding:
            logging.info(f"Retrieving cached embedding for: {text_input.text[0:10]}...")
            return EmbeddingOutput(
                embedding=json.loads(cached_embedding),
                description="The list of float values representing the text embedding.",
            )
        else:
            try:
                logging.info(f"Generating embedding for: {text_input.text[0:10]}...")
                embedding = handler.embed(text_input.text)
                logging.info(f"Setting embedding for: {text_input.text[0:10]}...")
                database_object.client.set(text_input.text, json.dumps(embedding))
                return EmbeddingOutput(
                    embedding=embedding,
                    description="The list of float values representing the text embedding.",
                )
            except RuntimeError:
                HTTPException(
                    status_code=404,
                    detail="Something went wrong with creating an embedding.",
                )
    else:
        logging.info(f"Generating embedding for: {text_input.text[0:10]}...")
        embedding = handler.embed(text_input.text)
        return EmbeddingOutput(
                    embedding=embedding,
                    description="The list of float values representing the text embedding.",
                )

@embed_router.post("/similarity")
async def calculate_similarity(
    text_1: TextInput, text_2: TextInput
) -> SimilarityOutput:
    """
    Compute the cosine similarity between two input texts.

    :param text_1: The first text.
    :param text_2: The second text.
    :return: The similarity score between the two input texts as JSON.
    """
    similarity_score = handler.similarity(text_1=text_1.text, text_2=text_2.text)
    return SimilarityOutput(
        similarity=similarity_score,
        description="Cosine similarity indicating semantic similarity. A value close to 1.0 is very similar, close to 0.0 close to -1.0 means little to no similarity, is very dissimilar.",
    )
