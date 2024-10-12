from fastapi import FastAPI
import json
from model import Handler
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
    embedding = handler.embed(text_input.text)
    return EmbeddingOutput(embedding=embedding, description="The list of float values representing the text embedding.")


@app.post("/similarity")
async def calculate_similarity(text_1: TextInput, text_2: TextInput) -> SimilarityOutput:
    similarity_score = handler.similarity(text_1=text_1.text, text_2=text_2.text)
    return SimilarityOutput(similarity=similarity_score, description="Value explaining similarity.")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8080, reload=True)
