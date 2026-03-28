"""Unit tests for Unpaywall ingester."""

import json
from unittest.mock import MagicMock, Mock, patch

import pytest

from data_pipeline.unpaywall_ingester import UnpaywallIngester


@pytest.fixture
def mock_storage():
    """Mock Google Cloud Storage client."""
    with patch("data_pipeline.unpaywall_ingester.storage") as mock:
        yield mock


@pytest.fixture
def ingester(mock_storage):
    """Create an ingester instance with mocked storage."""
    mock_storage.Client.return_value = MagicMock()
    return UnpaywallIngester(
        gcs_bucket="test-bucket",
        email="test@example.com",
    )


class TestUnpaywallIngester:
    """Test cases for UnpaywallIngester."""

    def test_initialization(self, ingester):
        """Test ingester initialization."""
        assert ingester.gcs_bucket == "test-bucket"
        assert ingester.email == "test@example.com"

    @patch("data_pipeline.unpaywall_ingester.requests.get")
    def test_fetch_paper_success(self, mock_get, ingester):
        """Test successful paper fetch."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "doi": "10.1234/test",
            "is_oa": True,
            "title": "Test Paper",
        }
        mock_get.return_value = mock_response

        result = ingester._fetch_paper("10.1234/test")

        assert result["is_oa"] is True
        assert result["title"] == "Test Paper"
        mock_get.assert_called_once()

    @patch("data_pipeline.unpaywall_ingester.requests.get")
    def test_fetch_paper_failure(self, mock_get, ingester):
        """Test paper fetch with API error."""
        mock_get.side_effect = Exception("API Error")

        result = ingester._fetch_paper("10.1234/test")

        assert result is None

    def test_store_paper(self, ingester):
        """Test storing paper metadata."""
        paper = {
            "doi": "10.1234/test",
            "title": "Test Paper",
            "is_oa": True,
        }

        ingester._store_paper(paper, "20240101")

        # Verify blob upload was called
        ingester.bucket.blob.assert_called_once()
        call_args = ingester.bucket.blob.call_args
        assert "unpaywall/papers/20240101" in call_args[0][0]

    def test_ingest_papers_with_valid_dois(self, ingester):
        """Test ingesting multiple papers."""
        dois = ["10.1234/test1", "10.1234/test2"]

        with patch.object(
            ingester, "_fetch_paper"
        ) as mock_fetch, patch.object(ingester, "_store_paper") as mock_store:
            mock_fetch.side_effect = [
                {"doi": "10.1234/test1", "is_oa": True},
                {"doi": "10.1234/test2", "is_oa": True},
            ]

            stats = ingester.ingest_papers(dois)

            assert stats["total_requested"] == 2
            assert stats["successful"] == 2
            assert mock_store.call_count == 2

    def test_ingest_papers_with_mixed_results(self, ingester):
        """Test ingesting papers with some failures."""
        dois = ["10.1234/test1", "10.1234/test2"]

        with patch.object(
            ingester, "_fetch_paper"
        ) as mock_fetch, patch.object(ingester, "_store_paper"):
            mock_fetch.side_effect = [
                {"doi": "10.1234/test1", "is_oa": True},
                None,  # Failed fetch
            ]

            stats = ingester.ingest_papers(dois)

            assert stats["total_requested"] == 2
            assert stats["successful"] == 1
            assert stats["failed"] == 1

    def test_custom_date_prefix(self, ingester):
        """Test using custom date prefix for storage."""
        dois = ["10.1234/test"]

        with patch.object(
            ingester, "_fetch_paper"
        ) as mock_fetch, patch.object(ingester, "_store_paper") as mock_store:
            mock_fetch.return_value = {"doi": "10.1234/test", "is_oa": True}

            ingester.ingest_papers(dois, date_prefix="20250101")

            mock_store.assert_called_once()
            call_args = mock_store.call_args
            assert call_args[0][1] == "20250101"

    def test_ingest_daily_from_crossref(self, ingester):
        """Test ingesting papers from CrossRef."""
        with patch.object(
            ingester, "_fetch_crossref_papers"
        ) as mock_crossref, patch.object(
            ingester, "_fetch_paper_unpaywall"
        ) as mock_unpaywall, patch.object(ingester, "_store_paper") as mock_store:
            mock_crossref.return_value = [
                {"doi": "10.1234/test1", "title": "Paper 1"},
                {"doi": "10.1234/test2", "title": "Paper 2"},
            ]
            mock_unpaywall.side_effect = [
                {"doi": "10.1234/test1", "is_oa": True},
                {"doi": "10.1234/test2", "is_oa": False},
            ]

            stats = ingester.ingest_daily_from_crossref(days_back=1)

            assert stats["total_papers_found"] == 2
            assert stats["successful_oa"] == 1

    @patch("data_pipeline.unpaywall_ingester.requests.get")
    def test_fetch_crossref_papers(self, mock_get, ingester):
        """Test fetching papers from CrossRef."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "message": {
                "items": [
                    {
                        "DOI": "10.1234/test1",
                        "title": ["Test Paper 1"],
                        "author": [{"given": "John", "family": "Doe"}],
                        "published-online": {"date-parts": [[2024, 1, 15]]},
                        "type": "journal-article",
                    }
                ]
            }
        }
        mock_get.return_value = mock_response

        papers = ingester._fetch_crossref_papers("2024-01-15")

        assert len(papers) >= 1
        assert papers[0]["doi"] == "10.1234/test1"
        assert "test paper 1" in papers[0]["title"].lower()

    @patch("data_pipeline.unpaywall_ingester.requests.get")
    def test_fetch_crossref_papers_empty(self, mock_get, ingester):
        """Test CrossRef fetch with no results."""
        mock_response = Mock()
        mock_response.json.return_value = {"message": {"items": []}}
        mock_get.return_value = mock_response

        papers = ingester._fetch_crossref_papers("2024-01-15")

        assert len(papers) == 0

    def test_fetch_paper_unpaywall_alias(self, ingester):
        """Test that _fetch_paper_unpaywall is an alias for _fetch_paper."""
        with patch.object(ingester, "_fetch_paper") as mock_fetch:
            mock_fetch.return_value = {"doi": "10.1234/test", "is_oa": True}

            result = ingester._fetch_paper_unpaywall("10.1234/test")

            assert result["is_oa"] is True
            mock_fetch.assert_called_once_with("10.1234/test")
