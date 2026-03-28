# Cloud Run Job for Unpaywall paper ingestion
# This Terraform configuration creates a scheduled Cloud Run job that ingests
# papers from Unpaywall and stores them in Google Cloud Storage.

terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP Region"
  type        = string
  default     = "us-central1"
}

variable "gcs_bucket" {
  description = "Google Cloud Storage bucket for storing papers"
  type        = string
}

variable "unpaywall_email" {
  description = "Email for Unpaywall API"
  type        = string
  sensitive   = true
}

variable "container_image" {
  description = "Container image URI for the Cloud Run job"
  type        = string
}

variable "schedule_frequency" {
  description = "Cron schedule for job execution (e.g., '0 2 * * *' for 2 AM daily)"
  type        = string
  default     = "0 2 * * *" # Daily at 2 AM UTC
}

variable "job_timeout" {
  description = "Job timeout in seconds"
  type        = number
  default     = 3600 # 1 hour
}

variable "days_back" {
  description = "Number of days to look back when fetching from CrossRef (1-30)"
  type        = number
  default     = 1

  validation {
    condition     = var.days_back > 0 && var.days_back <= 30
    error_message = "days_back must be between 1 and 30"
  }
}

# Service account for the Cloud Run job
resource "google_service_account" "unpaywall_job" {
  account_id   = "unpaywall-ingestion-job"
  display_name = "Unpaywall Ingestion Job Service Account"
}

# Grant Cloud Storage write access
resource "google_storage_bucket_iam_member" "job_storage_access" {
  bucket = var.gcs_bucket
  role   = "roles/storage.objectCreator"
  member = google_service_account.unpaywall_job.member
}

# Cloud Run Job
resource "google_cloud_run_v2_job" "unpaywall_ingestion" {
  name     = "unpaywall-ingestion-job"
  location = var.region

  deletion_protection = false

  template {
    parallelism             = 1
    task_count              = 1
    timeout                 = "${var.job_timeout}s"
    service_account         = google_service_account.unpaywall_job.email
    execution_environment   = "GEN2"
    max_retries             = 1

    containers {
      image = var.container_image

      env {
        name  = "GCS_BUCKET"
        value = var.gcs_bucket
      }

      env {
        name  = "UNPAYWALL_EMAIL"
        value = var.unpaywall_email
      }

      env {
        name  = "DAYS_BACK"
        value = tostring(var.days_back)
      }

      resources {
        limits = {
          cpu    = "2"
          memory = "2Gi"
        }
      }
    }
  }

  depends_on = [
    google_storage_bucket_iam_member.job_storage_access,
  ]
}

# Cloud Scheduler to trigger the job on a schedule
resource "google_cloud_scheduler_job" "unpaywall_trigger" {
  name             = "unpaywall-ingestion-trigger"
  description      = "Triggers Unpaywall ingestion job on a schedule"
  schedule         = var.schedule_frequency
  time_zone        = "UTC"
  attempt_deadline = "320s"
  region           = var.region

  retry_config {
    retry_count = 1
  }

  http_target {
    http_method = "POST"
    uri         = "https://${var.region}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${var.project_id}/jobs/${google_cloud_run_v2_job.unpaywall_ingestion.name}:run"

    headers = {
      "Content-Type" = "application/json"
    }

    auth_header {
      service_account_email = google_service_account.unpaywall_job.email
    }

    body = jsonencode({})
  }

  depends_on = [google_cloud_run_v2_job.unpaywall_ingestion]
}

# Output the job name for reference
output "job_name" {
  value       = google_cloud_run_v2_job.unpaywall_ingestion.name
  description = "Name of the Cloud Run job"
}

output "scheduler_job_name" {
  value       = google_cloud_scheduler_job.unpaywall_trigger.name
  description = "Name of the Cloud Scheduler job"
}
