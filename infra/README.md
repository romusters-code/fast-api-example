Introduction

Build and push Docker container so that it can be used in function app.

Build: 

`docker build -f Dockerfile -t embedding_service:latest . `


Login: 

`az acr login --name EmbeddingContainerRegistry `

Tag: 

`docker tag embedding_service:latest embeddingcontainerregistry.azurecr.io/embedding_service:latest`

Push: 

`docker push embeddingcontainerregistry.azurecr.io/embedding_service:latest`



`az login terraform`

`terraform init` 

`terraform plan` 

`terraform apply`

