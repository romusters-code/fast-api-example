# Quick Start: Daily CrossRef + Unpaywall Cloud Run Job

Automatically fetches papers published each day from CrossRef, checks Unpaywall for open access status, and stores them in Cloud Storage.

## 1. Prepare Configuration

```bash
cd infra/
cp terraform.tfvars.example terraform.tfvars

# Edit terraform.tfvars - set project_id, gcs_bucket, unpaywall_email
# Configure days_back if needed (default: 1 = yesterday)
```

## 2. Build & Push Docker Image

```bash
# Authenticate Docker with Artifact Registry
gcloud auth configure-docker europe-west4-docker.pkg.dev

# Build the image
docker build -f data-pipeline/Dockerfile \
  -t europe-west4-docker.pkg.dev/fastapi-449213/portfolio/unpaywall-ingestion:latest .

# Push to Artifact Registry
docker push europe-west4-docker.pkg.dev/fastapi-449213/portfolio/unpaywall-ingestion:latest
```

## 3. Deploy to Cloud Run

### Option A: Using Terraform (Recommended)

```bash
cd infra/
terraform init
terraform plan
terraform apply
```

### Option B: Using gcloud CLI

```bash
# Set variables
PROJECT_ID="fastapi-449213"
REGION="europe-west4"
GCS_BUCKET="data-pipeline-job"
UNPAYWALL_EMAIL="romusters@gmail.com"
CONTAINER_IMAGE="europe-west4-docker.pkg.dev/fastapi-449213/portfolio/unpaywall-ingestion:latest"
DAYS_BACK=1

# 1. Create service account
gcloud iam service-accounts create unpaywall-ingestion-job \
  --display-name="Unpaywall Ingestion Job Service Account" \
  --project=$PROJECT_ID

# 2. Grant Cloud Storage access
gcloud storage buckets add-iam-policy-binding gs://$GCS_BUCKET \
  --member=serviceAccount:unpaywall-ingestion-job@$PROJECT_ID.iam.gserviceaccount.com \
  --role=roles/storage.objectCreator

# 3. Create Cloud Run Job
gcloud run jobs create unpaywall-ingestion-job \
  --image=$CONTAINER_IMAGE \
  --region=$REGION \
  --set-env-vars=GCS_BUCKET=$GCS_BUCKET,UNPAYWALL_EMAIL=$UNPAYWALL_EMAIL,DAYS_BACK=$DAYS_BACK \
  --service-account=unpaywall-ingestion-job@$PROJECT_ID.iam.gserviceaccount.com \
  --task-timeout=3600s \
  --memory=2Gi \
  --cpu=2 \
  --project=$PROJECT_ID

# 4. Create Cloud Scheduler to trigger job daily at 2 AM UTC
gcloud scheduler jobs create app-engine unpaywall-ingestion-trigger \
  --schedule="0 2 * * *" \
  --http-method=POST \
  --uri=https://$REGION-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/$PROJECT_ID/jobs/unpaywall-ingestion-job:run \
  --oidc-service-account-email=unpaywall-ingestion-job@$PROJECT_ID.iam.gserviceaccount.com \
  --location=$REGION \
  --project=$PROJECT_ID
```

### Option C: Run Container Locally (for testing)

```bash
# Set environment variables
export GCS_BUCKET="your-bucket-name"
export UNPAYWALL_EMAIL="your-email@example.com"
export DAYS_BACK=1

# Option 1: Run with local image (if you built it)
docker run --rm \
  -e GCS_BUCKET=$GCS_BUCKET \
  -e UNPAYWALL_EMAIL=$UNPAYWALL_EMAIL \
  -e DAYS_BACK=$DAYS_BACK \
  -v ~/.config/gcloud:/root/.config/gcloud \
  europe-west4-docker.pkg.dev/fastapi-449213/portfolio/unpaywall-ingestion:latest

# Option 2: Pull and run from Artifact Registry
docker pull europe-west4-docker.pkg.dev/fastapi-449213/portfolio/unpaywall-ingestion:latest

docker run --rm \
  -e GCS_BUCKET=$GCS_BUCKET \
  -e UNPAYWALL_EMAIL=$UNPAYWALL_EMAIL \
  -e DAYS_BACK=$DAYS_BACK \
  -v ~/.config/gcloud:/root/.config/gcloud \
  europe-west4-docker.pkg.dev/fastapi-449213/portfolio/unpaywall-ingestion:latest

# Option 3: Run with credentials file (for CI/CD)
docker run --rm \
  -e GOOGLE_APPLICATION_CREDENTIALS=/tmp/gcp-key.json \
  -e GCS_BUCKET=$GCS_BUCKET \
  -e UNPAYWALL_EMAIL=$UNPAYWALL_EMAIL \
  -e DAYS_BACK=$DAYS_BACK \
  -v /path/to/gcp-key.json:/tmp/gcp-key.json:ro \
  europe-west4-docker.pkg.dev/fastapi-449213/portfolio/unpaywall-ingestion:latest
```

**Notes for local testing:**
- `-v ~/.config/gcloud:/root/.config/gcloud` - Mounts gcloud credentials into container
- `--rm` - Removes container after execution
- You need to be authenticated with GCP: `gcloud auth application-default login`
- Make sure your GCP user has Cloud Storage write permissions

```bash
# Check job status
gcloud run jobs describe unpaywall-ingestion-job --region europe-west4

# Check scheduler (runs daily at 2 AM UTC)
gcloud scheduler jobs describe unpaywall-ingestion-trigger --location europe-west4
```

## 5. View Results (Next Day)

```bash
# After job runs, check papers stored
gsutil ls gs://YOUR_BUCKET/unpaywall/papers/$(date +%Y%m%d)/

# View ingestion statistics
gsutil cat gs://YOUR_BUCKET/unpaywall/logs/$(date +%Y%m%d)/ingestion_log.json
```

## Manual Execution

```bash
# Run today's papers immediately
gcloud run jobs execute unpaywall-ingestion-job \
  --region europe-west4

# Run with custom days back
gcloud run jobs execute unpaywall-ingestion-job \
  --region europe-west4 \
  --set-env-vars="DAYS_BACK=7"

# View logs
gcloud logging read "resource.type=cloud_run_job" --limit 50
```

## What Gets Stored?

- ~1,500 papers found from CrossRef daily
- ~450 papers with open access (30% typical)
- Stored as JSON in: `gs://bucket/unpaywall/papers/YYYYMMDD/`
- Statistics saved in: `gs://bucket/unpaywall/logs/YYYYMMDD/ingestion_log.json`

## Files Reference

| File | Purpose |
|------|---------|
| `data-pipeline/unpaywall_ingester.py` | Core ingestion logic (CrossRef + Unpaywall) |
| `data-pipeline/main.py` | Cloud Run entry point |
| `data-pipeline/Dockerfile` | Container definition |
| `infra/unpaywall_job.tf` | Terraform infrastructure |
| `data-pipeline/UNPAYWALL_JOB.md` | Full documentation |

## Key Configuration

In `terraform.tfvars`:
- `project_id` - Your GCP project
- `gcs_bucket` - Cloud Storage bucket
- `unpaywall_email` - Email registered with Unpaywall
- `days_back` - How many days to look back (1-30, default: 1)
- `schedule_frequency` - Cron schedule (default: `0 2 * * *` = daily 2 AM UTC)

