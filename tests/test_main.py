import pytest
from fastapi.testclient import TestClient
from app.main import app, EmbeddingOutput, TextInput
from pydantic import BaseModel

# Arrange
client = TestClient(app)

def test_embed_text(long_string_input):

    # Act: Send a POST request to the /embed endpoint
    response = client.post("/embed", json=long_string_input)

    # Assert the response status code
    assert response.status_code == 200

    # Assert the response data structure
    response_data = response.json()
    assert "embedding" in response_data
    assert "description" in response_data
    assert response_data["description"] == "The list of float values representing the text embedding."

    # Assert the embedding values
    assert isinstance(response_data["embedding"], list)
    assert len(response_data["embedding"]) > 0  # Ensure it's a non-empty list
