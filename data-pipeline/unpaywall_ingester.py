"""Ingestion job for papers from Unpaywall and CrossRef APIs."""

import json
import logging
from datetime import datetime, timedelta
from typing import Optional
from urllib.parse import urlencode

import requests
import urllib3
from google.cloud import storage

# Suppress InsecureRequestWarning from urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class UnpaywallIngester:
    """Ingests open access papers from Unpaywall API and CrossRef, stores in Cloud Storage."""

    UNPAYWALL_BASE_URL = "https://api.unpaywall.org/v2"
    CROSSREF_BASE_URL = "https://api.crossref.org/v1"
    BATCH_SIZE = 100

    def __init__(
        self,
        gcs_bucket: str,
        email: str,
        gcs_project_id: Optional[str] = None,
    ):
        """
        Initialize the Unpaywall ingester.

        Args:
            gcs_bucket: Google Cloud Storage bucket name
            email: Email for Unpaywall API (required by API)
            gcs_project_id: GCP project ID (optional, uses default if not provided)
        """
        self.gcs_bucket = gcs_bucket
        self.email = email
        self.storage_client = storage.Client(project=gcs_project_id)
        self.bucket = self.storage_client.bucket(gcs_bucket)

 
    def ingest_daily_from_crossref(
        self,
        days_back: int = 1,
        limit_per_day: int = 1000,
        download_pdfs: bool = False,
        date_prefix: Optional[str] = None,
    ) -> dict:
        """
        Ingest papers from CrossRef published in the last N days, check Unpaywall for OA.

        Args:
            days_back: Number of days to look back (1 = yesterday, 2 = last 2 days, etc.)
            limit_per_day: Maximum papers per day from CrossRef
            download_pdfs: Whether to download PDF files from Unpaywall
            date_prefix: Optional custom date prefix for storage path

        Returns:
            Dictionary with ingestion statistics
        """
        if not date_prefix:
            date_prefix = datetime.utcnow().strftime("%Y%m%d")

        stats = {
            "source": "crossref",
            "days_back": days_back,
            "download_pdfs": download_pdfs,
            "total_papers_found": 0,
            "successful_oa": 0,
            "pdfs_downloaded": 0,
            "failed": 0,
            "timestamp": datetime.utcnow().isoformat(),
            "failed_dois": [],
        }

        for day_offset in range(days_back):
            target_date = datetime.utcnow() - timedelta(days=day_offset + 1)
            date_str = target_date.strftime("%Y-%m-%d")

            logger.info(f"Fetching {limit_per_day} papers from {date_str}")

            papers = self._fetch_crossref_papers(date_str, limit_per_day)
            logger.info(f"Found {len(papers)} papers from {date_str}")

            for paper in papers:
                stats["total_papers_found"] += 1

                try:
                    doi = paper.get("doi")
                    if not doi:
                        logger.warning("Paper without DOI, skipping")
                        continue

                    oa_data = self._fetch_paper_unpaywall(doi)
                    if oa_data and oa_data.get("is_oa"):
                        self._store_paper(oa_data, date_prefix)
                        stats["successful_oa"] += 1
                        
                        # Download PDF if requested
                        if download_pdfs:
                            if self._download_pdf(oa_data, date_prefix):
                                stats["pdfs_downloaded"] += 1
                    else:
                        logger.debug(f"Paper not OA or not indexed: {doi}")

                except Exception as e:
                    logger.error(f"Failed to process paper: {str(e)}")
                    stats["failed"] += 1
                    stats["failed_dois"].append(paper.get("doi"))

                if stats["total_papers_found"] % 100 == 0:
                    logger.info(
                        f"Processed {stats['total_papers_found']} papers "
                        f"({stats['successful_oa']} OA, {stats['pdfs_downloaded']} PDFs)"
                    )

        self._store_ingestion_log(stats, date_prefix)
        return stats

    def _fetch_paper(self, doi: str) -> Optional[dict]:
        """
        Fetch paper metadata from Unpaywall API.

        Args:
            doi: Digital Object Identifier

        Returns:
            Paper metadata dictionary or None if not found
        """
        try:
            url = f"{self.UNPAYWALL_BASE_URL}/{doi}"
            params = {"email": self.email}
            response = requests.get(url, params=params, timeout=10, verify=False)
            if response.status_code == 404:
                logger.debug(f"DOI not found in Unpaywall: {doi}")
                return None
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"API error fetching DOI {doi}: {str(e)}")
            return None

    def _fetch_paper_unpaywall(self, doi: str) -> Optional[dict]:
        """Alias for _fetch_paper for clarity."""
        return self._fetch_paper(doi)

    def _fetch_crossref_papers(self, date: str, limit: int = 10) -> list[dict]:
        """
        Fetch papers published on a specific date from CrossRef API.

        Args:
            date: Date string in YYYY-MM-DD format
            limit: Maximum number of results

        Returns:
            List of paper metadata dictionaries
        """
        try:
            papers = []
            url = f"{self.CROSSREF_BASE_URL}/works"

            # Query papers from specific date
            params = {
                "filter": f"from-pub-date:{date},until-pub-date:{date}",
                "rows": min(1000, limit),  # CrossRef max is 1000 per request
                "sort": "published",
                "order": "asc",
                "select": "DOI,title,author,published-online,type",
            }

            offset = 0
            while len(papers) < limit:
                params["offset"] = offset
                response = requests.get(url, params=params, timeout=15, verify=False)
                response.raise_for_status()

                data = response.json()
                items = data.get("message", {}).get("items", [])

                if not items:
                    break

                for item in items:
                    if len(papers) >= limit:
                        break

                    doi = item.get("DOI")
                    if doi:
                        papers.append({
                            "doi": doi,
                            "title": item.get("title", [""])[0] if item.get("title") else "",
                            "authors": item.get("author", []),
                            "published": item.get("published-online", {}).get("date-parts", [[None]])[0],
                            "type": item.get("type"),
                        })

                offset += len(items)
                logger.debug(f"Fetched {len(papers)} papers from CrossRef")

            logger.info(f"Retrieved {len(papers)} papers from CrossRef for {date}")
            return papers

        except requests.exceptions.RequestException as e:
            logger.error(f"CrossRef API error: {str(e)}")
            return []

    def _store_paper(self, paper: dict, date_prefix: str) -> None:
        """
        Store paper metadata in Cloud Storage.

        Args:
            paper: Paper metadata dictionary
            date_prefix: Date prefix for storage path (YYYYMMDD format)
        """
        doi = paper.get("doi", "unknown").replace("/", "_")
        blob_name = f"unpaywall/papers/{date_prefix}/{doi}.json"

        blob = self.bucket.blob(blob_name)
        blob.upload_from_string(
            json.dumps(paper, indent=2),
            content_type="application/json",
        )
        logger.debug(f"Stored paper: {blob_name}")

    def _download_pdf(self, paper: dict, date_prefix: str) -> Optional[str]:
        """
        Download PDF from Unpaywall best OA location with validation.

        Args:
            paper: Paper metadata dictionary from Unpaywall
            date_prefix: Date prefix for storage path

        Returns:
            GCS blob name if successful, None otherwise
        """
        try:
            doi = paper.get("doi", "unknown").replace("/", "_")
            best_oa_location = paper.get("best_oa_location")

            if not best_oa_location:
                logger.debug(f"No OA location for {doi}")
                return None

            pdf_url = best_oa_location.get("url_for_pdf") or best_oa_location.get("url")
            if not pdf_url:
                logger.debug(f"No PDF URL available for {doi}")
                return None

            # Download PDF with retry logic
            logger.info(f"Downloading PDF for {doi} from {pdf_url}")
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "application/pdf"
            }
            
            max_retries = 2
            for attempt in range(max_retries + 1):
                try:
                    response = requests.get(
                        pdf_url, 
                        timeout=30, 
                        verify=False, 
                        headers=headers, 
                        allow_redirects=True,
                        stream=True
                    )
                    response.raise_for_status()
                    break
                except requests.exceptions.RequestException as e:
                    if attempt < max_retries:
                        logger.warning(f"Download attempt {attempt + 1} failed for {doi}, retrying...")
                        continue
                    raise

            # Read content with size limit (50MB max)
            max_size = 50 * 1024 * 1024
            content = b""
            for chunk in response.iter_content(chunk_size=8192):
                content += chunk
                if len(content) > max_size:
                    logger.warning(f"PDF too large for {doi}: exceeded {max_size} bytes")
                    return None

            # Comprehensive PDF validation
            if not self._is_valid_pdf(content, doi):
                return None

            # Store in Cloud Storage
            blob_name = f"unpaywall/pdfs/{date_prefix}/{doi}.pdf"
            blob = self.bucket.blob(blob_name)
            blob.upload_from_string(
                content,
                content_type="application/pdf",
            )
            logger.info(f"Stored PDF: {blob_name} ({len(content)} bytes)")
            return blob_name

        except requests.exceptions.RequestException as e:
            logger.warning(f"Failed to download PDF for {doi}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error storing PDF for {doi}: {str(e)}")
            return None

    def _is_valid_pdf(self, content: bytes, doi: str) -> bool:
        """
        Validate that content is a valid PDF file.

        Args:
            content: File content bytes
            doi: DOI for logging

        Returns:
            True if valid PDF, False otherwise
        """
        if len(content) < 100:
            logger.warning(f"PDF too small for {doi}: {len(content)} bytes")
            return False

        # Check PDF magic bytes/header
        if not content.startswith(b"%PDF"):
            logger.warning(f"Invalid PDF header for {doi}: {content[:20]}")
            return False

        # Check for PDF footer (should end with %%EOF)
        if not (b"%%EOF" in content[-20:] or b"%EOF" in content[-20:]):
            logger.warning(f"Missing PDF footer for {doi}")
            return False

        # Check for common corruption patterns (basic check)
        # If file contains too much non-ASCII content early on, it's likely corrupted
        try:
            # Try to find the xref table (valid PDFs have this)
            if b"xref" not in content:
                logger.warning(f"Missing xref table in PDF for {doi}")
                return False
        except Exception as e:
            logger.warning(f"PDF validation error for {doi}: {str(e)}")
            return False

        return True

    def _store_ingestion_log(self, stats: dict, date_prefix: str) -> None:
        """
        Store ingestion statistics to Cloud Storage.

        Args:
            stats: Ingestion statistics dictionary
            date_prefix: Date prefix for storage path
        """
        blob_name = f"unpaywall/logs/{date_prefix}/ingestion_log.json"
        blob = self.bucket.blob(blob_name)
        blob.upload_from_string(
            json.dumps(stats, indent=2),
            content_type="application/json",
        )
        logger.info(f"Ingestion log stored: {blob_name}")


def run_job(
    gcs_bucket: str,
    email: str,
) -> None:
    """
    Main job entry point for Cloud Run.

    Args:
        gcs_bucket: Google Cloud Storage bucket name
        email: Email for Unpaywall API
    """
    logger.info("Starting Unpaywall ingestion job")

    ingester = UnpaywallIngester(gcs_bucket=gcs_bucket, email=email)

    stats = ingester.ingest_daily_from_crossref(days_back=1)    

    logger.info(f"Job completed. Stats: {stats}")
