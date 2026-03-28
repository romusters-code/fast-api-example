# Unpaywall + CrossRef Ingestion Cloud Run Job

This document describes the Cloud Run job for ingesting open access papers from CrossRef and Unpaywall APIs, storing them in Google Cloud Storage.

## Overview

The job automatically fetches papers published each day from CrossRef API and checks Unpaywall for open access status.

**Workflow:**
- Queries CrossRef for papers published on a specific date
- For each paper, checks Unpaywall API for open access status
- Stores only OA papers in JSON format
- Logs ingestion statistics

```
Cloud Scheduler (Daily)
      ↓
Cloud Run Job
      ↓
CrossRef API (papers from date)
      ↓
Unpaywall API (check OA status)
      ↓
Cloud Storage (gs://bucket/unpaywall/papers/)
```

## Setup

### Prerequisites

1. **Google Cloud Project** with:
   - Cloud Run API enabled
   - Cloud Scheduler API enabled
   - Cloud Storage bucket created
   - Service Account with appropriate permissions

2. **Container Image** built and pushed to Artifact Registry or Container Registry

3. **Unpaywall Email**: Register at https://unpaywall.org/products/api to get API access

### Deployment

#### 1. Build and Push Docker Image

```bash
# From the repository root
docker build -f data-pipeline/Dockerfile -t gcr.io/PROJECT_ID/unpaywall-ingestion:latest .
docker push gcr.io/PROJECT_ID/unpaywall-ingestion:latest
```

#### 2. Deploy with Terraform

```bash
cd infra/

# Create terraform.tfvars
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your project details

# Deploy
terraform init
terraform plan
terraform apply
```

## Usage

### Running Manually

#### Ingest from Yesterday's CrossRef Papers

```bash
gcloud run jobs execute unpaywall-ingestion-job \
  --region us-central1
```

#### Ingest Last 7 Days

```bash
gcloud run jobs execute unpaywall-ingestion-job \
  --region us-central1 \
  --set-env-vars="DAYS_BACK=7"
```

### Scheduling

The job runs automatically via Cloud Scheduler based on the configured cron schedule. Default: Daily at 2 AM UTC.

**To modify the schedule:**

```bash
# Edit schedule_frequency in terraform.tfvars
terraform apply
```

## Environment Variables

| Variable | Description | Required | Example |
|----------|-------------|----------|---------|
| `GCS_BUCKET` | Cloud Storage bucket name | Yes | `my-papers-bucket` |
| `UNPAYWALL_EMAIL` | Email for Unpaywall API | Yes | `user@example.com` |
| `DAYS_BACK` | Days to look back (1-30) | No | `1` |

## Cloud Storage Structure

Papers are organized by ingestion date:

```
gs://your-bucket/
├── unpaywall/
│   ├── papers/
│   │   └── 20240115/
│   │       ├── 10_1234_test1.json
│   │       ├── 10_1234_test2.json
│   │       └── ...
│   └── logs/
│       └── 20240115/
│           └── ingestion_log.json
```

### Paper JSON Format

```json
{
  "doi": "10.1234/example",
  "title": "Example Paper Title",
  "authors": [...],
  "year": 2024,
  "is_oa": true,
  "oa_status": "gold",
  "oa_locations": [...],
  "best_oa_location": {...}
}
```

### Ingestion Log Format

```json
{
  "source": "crossref",
  "days_back": 1,
  "total_papers_found": 1500,
  "successful_oa": 450,
  "failed": 2,
  "timestamp": "2024-01-15T02:00:00",
  "failed_dois": ["10.1234/failed1"]
}
```

## Monitoring

### View Job Logs

```bash
gcloud run jobs describe unpaywall-ingestion-job --region us-central1
gcloud logging read "resource.type=cloud_run_job" --limit 50
```

### Check Ingestion Statistics

Papers and logs are stored in Cloud Storage:

```bash
# List papers from today
gsutil ls gs://your-bucket/unpaywall/papers/$(date +%Y%m%d)/

# View ingestion log
gsutil cat gs://your-bucket/unpaywall/logs/$(date +%Y%m%d)/ingestion_log.json
```

## API Rate Limiting

**CrossRef:** 50 requests/second (per IP)
**Unpaywall:** Generally lenient; includes email in user-agent

Current implementation includes:
- Batch processing with logging every 100 papers
- Retry logic (1 retry) for transient failures
- Configurable timeouts (15s for CrossRef, 10s for Unpaywall)

**Tips:**
- CrossRef returns 1000 papers max per request
- Job processes ~10-20 papers/second depending on API latency
- For 1 week of papers (~10,000 papers): ~10-15 minutes

## Cost Optimization

- **Job timeout**: Set to 3600s (1 hour) by default. Adjust based on volume
- **CPU/Memory**: 2 CPU, 2GB memory. Adjust via Terraform if needed
- **Storage**: Papers stored as JSON (~2-5 KB per paper typical)

Example cost estimate (daily):
- ~1,500 papers/day from CrossRef
- ~450 OA papers (30% typical OA rate)
- ~1-2 MB stored/day
- Cloud Storage: ~$0.02/month for storage
- Cloud Run: ~0.01 credits/day

## Troubleshooting

### Job Fails with "GCS_BUCKET not found"

Check the bucket exists and the service account has write access:

```bash
gsutil iam ch serviceAccount:unpaywall-ingestion-job@PROJECT_ID.iam.gserviceaccount.com:objectCreator gs://your-bucket
```

### High Failure Rate

- Check CrossRef/Unpaywall API status
- Review logs in Cloud Logging
- Monitor API response times

### Job Timeout

Increase timeout or reduce days_back:

```bash
# In terraform.tfvars
job_timeout = 7200  # 2 hours
terraform apply
```

## Development

### Local Testing

```bash
# Install dependencies
pip install -r requirements.txt
pip install requests google-cloud-storage

# Test CrossRef fetch
python -c "
from data_pipeline.unpaywall_ingester import UnpaywallIngester

ingester = UnpaywallIngester(
    gcs_bucket='test-bucket',
    email='your-email@example.com'
)

# Fetch papers from today
papers = ingester._fetch_crossref_papers('2024-01-15', limit=10)
for paper in papers:
    print(f\"Found: {paper['doi']} - {paper['title']}\")
"
```

### Run Tests

```bash
pytest tests/test_unpaywall_ingester.py -v
```

## API Reference

#### `ingest_daily_from_crossref(days_back: int = 1, limit_per_day: int = 10000, date_prefix: str = None) -> dict`

Ingest papers from CrossRef published in the last N days, check Unpaywall for OA.

**Parameters:**
- `days_back`: Number of days to look back (1 = yesterday)
- `limit_per_day`: Maximum papers per day from CrossRef
- `date_prefix`: Storage date prefix (default: YYYYMMDD)

**Returns:** Statistics dictionary

**Example:**
```python
stats = ingester.ingest_daily_from_crossref(days_back=1)
# Returns: {
#   "source": "crossref",
#   "days_back": 1,
#   "total_papers_found": 1500,
#   "successful_oa": 450,
#   "failed": 2,
#   ...
# }
```

#### `_fetch_crossref_papers(date: str, limit: int = 10000) -> list[dict]`

Fetch papers from CrossRef published on specific date.

**Parameters:**
- `date`: Date string (YYYY-MM-DD format)
- `limit`: Maximum results

## Links

- [CrossRef API Documentation](https://github.com/CrossRef/rest-api-doc)
- [Unpaywall API Documentation](https://unpaywall.org/products/api)
- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Cloud Scheduler Documentation](https://cloud.google.com/scheduler/docs)
- [Google Cloud Storage Documentation](https://cloud.google.com/storage/docs)

## Setup

### Prerequisites

1. **Google Cloud Project** with:
   - Cloud Run API enabled
   - Cloud Scheduler API enabled
   - Cloud Storage bucket created
   - Service Account with appropriate permissions

2. **Container Image** built and pushed to Artifact Registry or Container Registry

3. **Unpaywall Email**: Register at https://unpaywall.org/products/api to get API access

### Deployment

#### 1. Build and Push Docker Image

```bash
# From the repository root
docker build -f data-pipeline/Dockerfile -t gcr.io/PROJECT_ID/unpaywall-ingestion:latest .
docker push gcr.io/PROJECT_ID/unpaywall-ingestion:latest
```

#### 2. Deploy with Terraform

```bash
cd infra/

# Create terraform.tfvars
cat > terraform.tfvars << EOF
project_id = "YOUR_PROJECT_ID"
region = "us-central1"
gcs_bucket = "your-bucket-name"
unpaywall_email = "your-email@example.com"
container_image = "gcr.io/YOUR_PROJECT_ID/unpaywall-ingestion:latest"
schedule_frequency = "0 2 * * *"  # Daily at 2 AM UTC
EOF

# Deploy
terraform init
terraform plan
terraform apply
```

## Usage

### Running Manually

#### Ingest Specific DOIs

```bash
gcloud run jobs execute unpaywall-ingestion-job \
  --region us-central1 \
  --set-env-vars="DOIS=10.1234/test1,10.1234/test2"
```

#### Ingest by Query

```bash
gcloud run jobs execute unpaywall-ingestion-job \
  --region us-central1 \
  --set-env-vars="QUERY=machine learning"
```

### Scheduling

The job runs automatically via Cloud Scheduler based on the configured cron schedule. Default: Daily at 2 AM UTC.

**To modify the schedule:**

```bash
# Edit the schedule_frequency variable in terraform.tfvars
terraform apply
```

## Environment Variables

| Variable | Description | Required | Example |
|----------|-------------|----------|---------|
| `GCS_BUCKET` | Cloud Storage bucket name | Yes | `my-papers-bucket` |
| `UNPAYWALL_EMAIL` | Email for Unpaywall API | Yes | `user@example.com` |
| `DOIS` | Comma-separated list of DOIs | No | `10.1234/test1,10.1234/test2` |
| `QUERY` | Search query (not fully supported) | No | `machine learning` |

## Cloud Storage Structure

Papers are organized by ingestion date:

```
gs://your-bucket/
├── unpaywall/
│   ├── papers/
│   │   └── 20240115/
│   │       ├── 10_1234_test1.json
│   │       ├── 10_1234_test2.json
│   │       └── ...
│   └── logs/
│       └── 20240115/
│           └── ingestion_log.json
```

### Paper JSON Format

```json
{
  "doi": "10.1234/example",
  "title": "Example Paper Title",
  "authors": [...],
  "year": 2024,
  "is_oa": true,
  "oa_status": "gold",
  "oa_locations": [...],
  "best_oa_location": {...}
}
```

### Ingestion Log Format

```json
{
  "total_requested": 100,
  "successful": 98,
  "failed": 2,
  "timestamp": "2024-01-15T02:00:00",
  "failed_dois": ["10.1234/failed1", "10.1234/failed2"]
}
```

## Monitoring

### View Job Logs

```bash
gcloud run jobs describe unpaywall-ingestion-job --region us-central1
gcloud logging read "resource.type=cloud_run_job" --limit 50
```

### Check Ingestion Statistics

Papers and logs are stored in Cloud Storage:

```bash
gsutil ls gs://your-bucket/unpaywall/papers/
gsutil cat gs://your-bucket/unpaywall/logs/20240115/ingestion_log.json
```

## API Rate Limiting

The Unpaywall API is rate-limited. Current implementation includes:
- 10-second timeout per request
- Batch processing with logging every 10 papers
- Retry logic (1 retry) for transient failures

**Tips:**
- Space out bulk ingestions to avoid hitting rate limits
- Monitor failed DOIs in the ingestion log
- Stagger multiple job executions if needed

## Cost Optimization

- **Job timeout**: Set to 3600s (1 hour) by default. Adjust based on volume
- **CPU/Memory**: 2 CPU, 2GB memory. Adjust via Terraform if needed
- **Storage**: Papers stored as JSON (~1-5 KB per paper typical)

Example cost estimate:
- 10,000 papers/month × 2 KB = ~20 GB storage
- Cloud Storage: ~$0.02/month for storage
- Cloud Run: ~$0.00 for 3600 execution seconds/month

## Troubleshooting

### Job Fails with "GCS_BUCKET not found"

Check the bucket exists and the service account has write access:

```bash
gsutil iam ch serviceAccount:unpaywall-ingestion-job@PROJECT_ID.iam.gserviceaccount.com:objectCreator gs://your-bucket
```

### High Failure Rate

- Check Unpaywall API status
- Verify DOIs are valid
- Review logs in Cloud Logging

### Job Timeout

Reduce the number of DOIs per execution or increase timeout:

```bash
# In terraform.tfvars
job_timeout = 7200  # 2 hours
terraform apply
```

## Development

### Local Testing

```bash
# Install dependencies
pip install -r requirements.txt
pip install requests google-cloud-storage

# Test the ingester
python -c "
from data_pipeline.unpaywall_ingester import UnpaywallIngester

ingester = UnpaywallIngester(
    gcs_bucket='test-bucket',
    email='your-email@example.com'
)

# Test fetch (requires GCP credentials for Cloud Storage)
result = ingester._fetch_paper('10.1371/journal.pbio.1001535')
print(result)
"
```

### Run Tests

```bash
pytest tests/test_unpaywall_ingester.py -v
```

## API Reference

### UnpaywallIngester

#### `ingest_papers(dois: list[str], date_prefix: str = None) -> dict`

Ingest papers by DOI.

**Parameters:**
- `dois`: List of DOI strings
- `date_prefix`: Storage date prefix (default: YYYYMMDD)

**Returns:** Statistics dictionary with `successful`, `failed`, `timestamp`, and `failed_dois`

#### `ingest_by_query(query: str, limit: int = 1000, date_prefix: str = None) -> dict`

Ingest papers by search query (limited support).

**Note:** Unpaywall API doesn't support full-text search. This method is a placeholder for custom search implementations.

## Links

- [Unpaywall API Documentation](https://unpaywall.org/products/api)
- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Cloud Scheduler Documentation](https://cloud.google.com/scheduler/docs)
- [Google Cloud Storage Documentation](https://cloud.google.com/storage/docs)
