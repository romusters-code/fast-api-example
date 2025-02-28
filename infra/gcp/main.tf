variable "project_id" {
  description = "project id"
  type        = string
  default     = "fastapi-449213"
}

variable "project" {
  description = "project"
  type        = string
  default     = "fastapi"
}


variable "region" {
  description = "The GCP region"
  type        = string
  default     = "europe-west4"
}


provider "google" {
  project = var.project_id
  region  = var.region
}

terraform {
  backend "gcs" {
    bucket  = "terraform-state-fast-api-example"   
    prefix  = "terraform/state" # Path within the bucket to store the state file                        
  }
}

# Container Registry: Images are stored in Artifact Registry
# The registry already exists
data "google_artifact_registry_repository" "container_registry" {
  repository_id = "fastapi-docker-repo"
#   format        = "DOCKER"
  location      = var.region
#   description   = "Docker repository for FastAPI images"
}

# Enable necessary APIs
resource "google_project_service" "container_registry"  {
  for_each = toset([
    "container.googleapis.com",
    "run.googleapis.com",
    "artifactregistry.googleapis.com"
  ])
  project = var.project_id
  service = each.key
}

resource "google_artifact_registry_repository" "python_registry" {
  location      = var.region
  repository_id = "python-package"
  description   = "python registry"
  format        = "PYTHON"
}

resource "google_project_service" "artifact_registry_api" {
  service = "artifactregistry.googleapis.com"
  project = var.project_id
}

# IAM Binding for Artifact Registry
resource "google_artifact_registry_repository_iam_binding" "artifact_registry_binding" {
  repository = data.google_artifact_registry_repository.container_registry.name
  role       = "roles/artifactregistry.writer"
  members    = ["serviceAccount:${data.google_service_account.cloud_run_service_account.email}"]
}

# Service Account for Cloud Run
data "google_service_account" "cloud_run_service_account" {
  account_id   = "cloud-run-service-account"
}

# Grant necessary roles to the Service Account
resource "google_project_iam_binding" "cloud_run_iam" {
  project = var.project_id
  role    = "roles/run.admin"
  members = ["serviceAccount:${data.google_service_account.cloud_run_service_account.email}"]
}

# Deploy FastAPI Docker app to Cloud Run
resource "google_cloud_run_service" "fastapi_service" {
  name     = "fastapi-service"
  location = var.region

  template {
    spec {
      containers {
        
        image = "${data.google_artifact_registry_repository.container_registry.location}-docker.pkg.dev/${var.project_id}/${data.google_artifact_registry_repository.container_registry.name}/fastapi:latest"
        resources {
          limits = {
            memory = "2048Mi"
            cpu    = "1"
          }
        }
        env {
          name  = "DATABASE_URL"
          value = "value1"
        }
        env {
          name  = "DATABASE_PORT"
          value = "value2"
        }
        env {
          name  = "DATABASE_KIND"
          value = "value3"
        }
        env {
          name  = "DATABASE_API_KEY"
          value = "value3"
        }
        env {
          name  = "CACHE_ENABLED"
          value = false
        }
      }
      service_account_name = data.google_service_account.cloud_run_service_account.email
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }
}

# Grant permissions to Cloud Run Invoker
resource "google_cloud_run_service_iam_binding" "invoker_permission" {
  service = google_cloud_run_service.fastapi_service.name
  location = var.region
  role    = "roles/run.invoker"
  members = ["allUsers"] # Allows public access; modify as needed
}