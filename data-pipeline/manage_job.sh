#!/bin/bash
# Helper script for managing the Unpaywall ingestion job

set -e

PROJECT_ID="${1:-}"
REGION="${2:-us-central1}"
ACTION="${3:-}"

if [ -z "$PROJECT_ID" ]; then
    echo "Usage: $0 <project_id> [region] <action>"
    echo ""
    echo "Actions:"
    echo "  build-image          Build and push Docker image to Container Registry"
    echo "  deploy               Deploy/update job with Terraform"
    echo "  run [dois|query]     Manually trigger the job"
    echo "  logs                 Show recent job logs"
    echo "  status               Show job status"
    echo "  delete               Delete the job and scheduler"
    exit 1
fi

case "$ACTION" in
    build-image)
        echo "Building Docker image..."
        docker build -f data-pipeline/Dockerfile \
            -t gcr.io/$PROJECT_ID/unpaywall-ingestion:latest \
            -t gcr.io/$PROJECT_ID/unpaywall-ingestion:$(date +%s) \
            .
        echo "Pushing image to Container Registry..."
        docker push gcr.io/$PROJECT_ID/unpaywall-ingestion:latest
        echo "Done! Update container_image in terraform.tfvars"
        ;;

    deploy)
        echo "Deploying with Terraform..."
        cd infra
        terraform init
        terraform plan -var="project_id=$PROJECT_ID" -var="region=$REGION"
        terraform apply -var="project_id=$PROJECT_ID" -var="region=$REGION"
        cd -
        echo "Deployment complete!"
        ;;

    run)
        echo "Triggering job execution..."
        if [ "$3" == "dois" ]; then
            read -p "Enter comma-separated DOIs: " dois
            gcloud run jobs execute unpaywall-ingestion-job \
                --project=$PROJECT_ID \
                --region=$REGION \
                --set-env-vars="DOIS=$dois"
        elif [ "$3" == "query" ]; then
            read -p "Enter search query: " query
            gcloud run jobs execute unpaywall-ingestion-job \
                --project=$PROJECT_ID \
                --region=$REGION \
                --set-env-vars="QUERY=$query"
        else
            gcloud run jobs execute unpaywall-ingestion-job \
                --project=$PROJECT_ID \
                --region=$REGION
        fi
        echo "Job triggered!"
        ;;

    logs)
        echo "Fetching recent logs..."
        gcloud logging read \
            "resource.type=cloud_run_job AND resource.labels.job_name=unpaywall-ingestion-job" \
            --project=$PROJECT_ID \
            --limit=50 \
            --format="table(timestamp,jsonPayload.message)" \
            --sort-by=timestamp.reverse
        ;;

    status)
        echo "Job status:"
        gcloud run jobs describe unpaywall-ingestion-job \
            --project=$PROJECT_ID \
            --region=$REGION \
            --format="table(name,status)"
        echo ""
        echo "Scheduler status:"
        gcloud scheduler jobs describe unpaywall-ingestion-trigger \
            --project=$PROJECT_ID \
            --location=$REGION \
            --format="table(name,schedule,state)"
        ;;

    delete)
        read -p "Are you sure? This will delete the job and scheduler. (y/N) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            cd infra
            terraform destroy -var="project_id=$PROJECT_ID" -var="region=$REGION"
            cd -
            echo "Deleted!"
        else
            echo "Aborted."
        fi
        ;;

    *)
        echo "Unknown action: $ACTION"
        exit 1
        ;;
esac
