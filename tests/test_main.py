import unittest
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from app.main import app
from app.main import TextInput

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
    assert (
        response_data["description"]
        == "The list of float values representing the text embedding."
    )

    # Assert the embedding values
    assert isinstance(response_data["embedding"], list)
    assert len(response_data["embedding"]) > 0  # Ensure it's a non-empty list


text_inputs = [
    {"text": ""},
    {"text": "This is a short sentence."},
    {
        "text": "This is a longer sentence, which contains more words and should still work correctly."
    },
]


@pytest.mark.parametrize("text_input", text_inputs)
def test_embed_text_parametrized(text_input):
    # Act: Send a POST request to the /embed endpoint
    response = client.post("/embed", json=text_input)

    # Assert the response status code
    assert response.status_code == 200

    # Assert the response data structure
    response_data = response.json()
    assert "embedding" in response_data
    assert "description" in response_data
    assert (
        response_data["description"]
        == "The list of float values representing the text embedding."
    )

    # Assert the embedding values
    assert isinstance(response_data["embedding"], list)
    assert len(response_data["embedding"]) > 0  # Ensure it's a non-empty list


class TestCalculateSimilarity(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    @patch("app.main.handler.similarity")  # Mock the similarity function
    def test_calculate_similarity(self, mock_similarity):
        # Arrange
        text_1 = TextInput(text="Dog")
        text_2 = TextInput(text="Cat")
        mock_similarity.return_value = (
            0.95  # Mock the return value of the similarity function
        )

        # Act
        response = self.client.post(
            "/similarity",
            json={"text_1": text_1.model_dump(), "text_2": text_2.model_dump()},
        )

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "similarity": 0.95,
                "description": "Cosine similarity indicating semantic similarity. A value close to 1.0 is very similar, close to 0.0 close to -1.0 means little to no similarity, is very dissimilar.",
            },
        )
        mock_similarity.assert_called_once_with(
            text_1="Dog", text_2="Cat"
        )  # Check if the handler was called with the correct parameters
