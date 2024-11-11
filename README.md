# Introduction
Personal code to showcase my abilities, such as:
1. Software Engineering in Python:

   2. Code (e.g. design patterns)
   
   3. Tests (unit and integration)
   
   4. Project tooling (pre-commit, Ruff)
   
2. Docker
3. Terraform
4. Cloud Engineering
5. DevOps 


# Prerequisites
- Python 3.12 and Pip/Poetry
- Docker
- Terraform
- Azure subscription
- Pre-commit
- Hadolint binary (when using pre-commit)


# How to run

## Python
To run the project locally using Python, run:

`poetry run fastapi run app/main.py --host 0.0.0.0 --port 8080`

TODO: try [uv](https://github.com/astral-sh/uv) instead of Poetry.

Go to e.g.: http://0.0.0.0:81/docs

## Tests

`poetry run pytest tests/`

## Docker

First navigate to the `function_app` folder and then build the container:

`docker build -t functionapp:latest .`

Then run the container:

`docker run -p 80:80 -it functionapp:latest`


## Docker-compose
Redis can be used as a backend to cache FastAPI requests.

Start the FastAPI and Redis database using: `docker-compose up`

To rebuild, run: `docker-compose up --build`


## Cloud

### Terraform

[Terraform information](infra/README.md)


### Azure
Use the function app to 
Go to e.g.: http://*.azurewebsites.com.

# TODO:
- fix infra bug:  [DEBUG] POST https://management.azure.com/subscriptions/<subscription>/resourceGroups/rg20embedding001/providers/Microsoft.App/containerApps/ca20embedding001/listSecrets?api-version=2023-05-01 (status: 500): retrying in 1s (9 left)

I do have the correct role set for the principal.


- devops pipeline
- integration test
- create package from model and handler so that I can use it in Docker image
- caching requests for FastAPI using external database

