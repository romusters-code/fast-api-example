# Explanation

To be able to push Docker images to the Artifact Registry, I used this blog:

https://medium.com/@carstensavage/integrate-workload-identity-federation-with-github-actions-google-cloud-1893306f75c5


The workload identity provider name can be found using:

`gcloud iam workload-identity-pools providers list --project=PROJECT_ID --location=global --workload-identity-pool=WORKLOAD_IDENTITY_POOL_NAME`

The Service account email is found in the GCP Service Account section.

Make sure the principal has the following roles: Artifact Registry Administrator and Storage Admin.