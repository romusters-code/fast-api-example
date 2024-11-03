import pytest

@pytest.fixture
def long_string_input():
    return {
        "text": "This is a very long string. " * 100
    }

@pytest.fixture
def mock_handler(mocker):
    """Mock the similarity handler."""
    return mocker.patch('model.handler.similarity')