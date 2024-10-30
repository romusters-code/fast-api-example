import pytest

@pytest.fixture
def long_string_input():
    return {
        "text": "This is a very long string. " * 100
    }