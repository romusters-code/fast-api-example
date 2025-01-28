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


# Enable necessary APIs
resource "google_project_service" "container_registry" {
  for_each = toset([
    "container.googleapis.com",
    "run.googleapis.com",
    "artifactregistry.googleapis.com"
  ])
  project = var.project_id
  service = each.key
}

resource "google_project_service" "artifact_registry_api" {
  service = "artifactregistry.googleapis.com"
  project = var.project_id
}

# Container Registry: Images are stored in Artifact Registry
resource "google_artifact_registry_repository" "container_registry" {
  repository_id = "fastapi-docker-repo"
  format        = "DOCKER"
  location      = var.region
  description   = "Docker repository for FastAPI images"
}

# IAM Binding for Artifact Registry
resource "google_artifact_registry_repository_iam_binding" "artifact_registry_binding" {
  repository = google_artifact_registry_repository.container_registry.name
  role       = "roles/artifactregistry.writer"
  members    = ["serviceAccount:${google_service_account.cloud_run_service_account.email}"]
}

# Service Account for Cloud Run
resource "google_service_account" "cloud_run_service_account" {
  account_id   = "cloud-run-service-account"
  display_name = "Cloud Run Service Account"
}

# Grant necessary roles to the Service Account
resource "google_project_iam_binding" "cloud_run_iam" {
  project = var.project_id
  role    = "roles/run.admin"
  members = ["serviceAccount:${google_service_account.cloud_run_service_account.email}"]
}

# Deploy FastAPI Docker app to Cloud Run
resource "google_cloud_run_service" "fastapi_service" {
  name     = "fastapi-service"
  location = var.region

  template {
    spec {
      containers {
        image = "${google_artifact_registry_repository.container_registry.location}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.container_registry.name}/fastapi:latest"
        resources {
          limits = {
            memory = "512Mi"
            cpu    = "1"
          }
        }
      }
      service_account_name = google_service_account.cloud_run_service_account.email
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