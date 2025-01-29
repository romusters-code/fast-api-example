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
- Pyenv
- Docker
- Terraform
- Azure subscription
- Pre-commit
- Hadolint binary (when using pre-commit)

## Ansible
Ansible can be used to install prerequisites: `ansible-playbook ansible/ansible.yaml --ask-become-pass -e @ansible/var.yaml`


# How to run
## Pyenv
Install correct Python version using Pyenv:

`pyenv install 3.12`

## Python

`poetry env use $(pyenv which python)`
`poetry install`

To run the project locally using Python, run:

`poetry run fastapi run app/main.py --host 0.0.0.0 --port 8080`

Go to e.g.: http://0.0.0.0:8080/docs

## Tests

`poetry run pytest tests/`

## Docker

First navigate to the `function_app` folder and then build the container:

`docker build -t functionapp:latest .`

Then run the container:

`docker run -p 80:80 -it functionapp:latest`


## Docker-compose
Redis can be used as a backend to cache FastAPI requests.

Start the FastAPI and Redis database using: `docker compose up`

To rebuild, run e.g.: `docker compose --env-file .env --file docker-compose-pinecone.yaml up --build`

> **_NOTE:_** **The code works independent on choice of database**.
Two databases are currently supported.
Additional databases could be added by implementing the interface.
The corresponding docker compose files are: `-redis` and `-pinecone`.

## Cloud

### Terraform

[Terraform information](infra/README.md)


### Azure
Use the function app to
Go to e.g.: http://*.azurewebsites.com.

# Remarks
Although unadvised, setting `PYTHONHTTPSVERIFY` to `false` circumpasses SSL certificate verification when behind proxy firewall. Installing the required certificates in `certifi`, local truststore or poetry configuration is preferred.

# TODO:
- fix infra bug:  [DEBUG] POST https://management.azure.com/subscriptions/<subscription>/resourceGroups/rg20embedding001/providers/Microsoft.App/containerApps/ca20embedding001/listSecrets?api-version=2023-05-01 (status: 500): retrying in 1s (9 left)

I do have the correct role set for the principal.

- make Redis asynchronous
- devops pipeline
- integration test
- create package from model and handler so that I can use it in Docker image
- try [uv](https://github.com/astral-sh/uv) instead of Poetry.

