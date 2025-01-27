from pydantic import BaseModel


class TextInput(BaseModel):
    text: str


class EmbeddingOutput(BaseModel):
    embedding: list[float]
    description: str | None = None


class SimilarityOutput(BaseModel):
    similarity: float
    description: str | None = None