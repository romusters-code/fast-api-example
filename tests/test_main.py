import json
import os
import unittest

from dotenv import load_dotenv

load_dotenv()  # This will load variables from .env

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
from parameterized import parameterized

from embedding_api.config.settings import Settings
from embedding_api.main import app
from embedding_api.schemas.default import TextInput
from tests.payload_tests import long_string_input


class TestEmbedEndpoint(unittest.TestCase):
    # Arrange
    def setUp(self):
        self.client = TestClient(app)

    @patch("embedding_api.api.endpoints.embed.handler")
    @patch("embedding_api.api.endpoints.embed.database_object")
    def test_embed_text_cached(self, mock_database_object, mock_handler_object):
        mock_database_object.get = MagicMock(return_value=json.dumps([0.1, 0.2, 0.3]))

        # Act: Send a POST request to the /embed endpoint
        response = self.client.post("/embed", json=long_string_input)

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
        assert response_data["embedding"] == [0.1, 0.2, 0.3]
        mock_database_object.get.assert_called_once_with(long_string_input["text"])
        mock_handler_object.embed.assert_not_called()

    @patch("embedding_api.api.endpoints.embed.handler")
    @patch("embedding_api.api.endpoints.embed.database_object")
    def test_embed_text_not_cached(self, mock_database_object, mock_handler_object):
        mock_database_object.get = MagicMock(return_value=None)
        mock_handler_object.embed = MagicMock(return_value=[1, 2, 3])

        # Act: Send a POST request to the /embed endpoint
        response = self.client.post("/embed", json=long_string_input)

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
        mock_database_object.get.assert_called_once_with(long_string_input["text"])
        mock_handler_object.embed.assert_called_once_with(long_string_input["text"])

    @parameterized.expand(
        [
            ({"text": ""},),
            ({"text": "This is a short sentence."},),
            (
                {
                    "text": "This is a longer sentence, which contains more words and should still work correctly."
                },
            ),
        ]
    )
    @patch("embedding_api.api.endpoints.embed.database_object")
    def test_embed_text_parametrized(self, text_input, mock_database_object):
        mock_database_object.get = MagicMock(return_value=None)
        # Act: Send a POST request to the /embed endpoint
        response = self.client.post("/embed", json=text_input)

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

    @patch(
        "embedding_api.api.endpoints.embed.handler.similarity"
    )  # Mock the similarity function
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
