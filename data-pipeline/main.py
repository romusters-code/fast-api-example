"""Cloud Run job entry point for daily CrossRef ingestion."""

import os
import sys

from unpaywall_ingester import UnpaywallIngester


def main():
    """Main entry point for Cloud Run job."""
    # Read environment variables
    gcs_bucket = os.getenv("GCS_BUCKET")
    email = os.getenv("UNPAYWALL_EMAIL")
    days_back = int(os.getenv("DAYS_BACK", "1"))
    download_pdfs = os.getenv("DOWNLOAD_PDFS", "true").lower() == "true"

    # Validate required variables
    if not gcs_bucket:
        raise ValueError("GCS_BUCKET environment variable is required")
    if not email:
        raise ValueError("UNPAYWALL_EMAIL environment variable is required")

    # Initialize ingester
    ingester = UnpaywallIngester(gcs_bucket=gcs_bucket, email=email)

    # Ingest from CrossRef
    print(f"Starting daily CrossRef ingestion (looking back {days_back} day(s))")
    if download_pdfs:
        print("⚠️  PDF download enabled - this may take longer")
    
    stats = ingester.ingest_daily_from_crossref(
        days_back=days_back,
        download_pdfs=download_pdfs,
    )

    print(f"Ingestion complete. Stats: {stats}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
