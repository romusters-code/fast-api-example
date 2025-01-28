# Google

To deploy the infra on Google, first authenticate:

`gcloud auth application-default login`

Set the project id:

`gcloud config set project <project_id>`

Enable gcloud service 'artifactregistry.googleapis.com':

`gcloud services enable artifactregistry.googleapis.com`

`terraform init`

`terraform plan`

`terraform apply`

## Push Docker container


`gcloud auth configure-docker europe-west4-docker.pkg.dev`

## Github Actions

The infrastructure can also be deployed using Github Actions