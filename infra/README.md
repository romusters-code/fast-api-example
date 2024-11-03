# Introduction

Terraform is infrastructure as code tool. The infrastructure we are making here contains a Docker registry and a Function app amongst other resources.
The Function App uses a Docker container which needs to be available first, so we build and push it in the next section. We might also choose to create a DevOps pipeline to do this for us.
Build and push Docker container so that it can be used in function app.

## How to run

### Docker

Build: 

`docker build -f Dockerfile -t embedding_service:latest . `


Login: 

`az acr login --name EmbeddingContainerRegistry `

Tag: 

`docker tag embedding_service:latest embeddingcontainerregistry.azurecr.io/embedding_service:latest`

Push: 

`docker push embeddingcontainerregistry.azurecr.io/embedding_service:latest`

### Terraform

Login:

`az login terraform`

Init:

`terraform init` 

Plan:

`terraform plan` 


Apply:

`terraform apply`

