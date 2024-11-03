from fastapi import FastAPI
from app.model import Handler
from pydantic import BaseModel


class TextInput(BaseModel):
    text: str

class EmbeddingOutput(BaseModel):
    embedding: list[float] 
    description: str | None = None

class SimilarityOutput(BaseModel):
    similarity: float
    description: str | None = None

app = FastAPI()

handler = Handler()

@app.post("/embed")
async def embed_text(text_input: TextInput) -> EmbeddingOutput:
    """
    Endpoint to creating embeddings from the input text.

    :param text_input: The text to embed.
    :return: The embedding of the input text as JSON.
    """
    embedding = handler.embed(text_input.text)
    return EmbeddingOutput(embedding=embedding, description="The list of float values representing the text embedding.")


@app.post("/similarity")
async def calculate_similarity(text_1: TextInput, text_2: TextInput) -> SimilarityOutput:
    """
    Compute the cosine similarity between two input texts.

    :param text_1: The first text.
    :param text_2: The second text.
    :return: The similarity score between the two input texts as JSON.
    """
    similarity_score = handler.similarity(text_1=text_1.text, text_2=text_2.text)
    return SimilarityOutput(similarity=similarity_score, description=
        "Cosine similarity indicating semantic similarity. A value close to 1.0 is very similar, close to 0.0 close to -1.0 means little to no similarity, is very dissimilar.")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8080, reload=True)
