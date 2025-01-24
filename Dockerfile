FROM python:3.12.6-slim-bookworm

WORKDIR /app

RUN apt-get update && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir --upgrade pip poetry  --trusted-host pypi.org --trusted-host files.pythonhosted.org

COPY pyproject.toml /app

# Be careful: this should not run in docker compose environment. It is only used to circumvent corporate proxy for personal projects.
RUN  poetry source add fpho https://files.pythonhosted.org && \
poetry config certificates.fpho.cert false && \
poetry source add pypi && \
poetry config certificates.PyPI.cert false && \
poetry config certificates.pypi.cert false 

ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_CACHE_DIR='/var/cache/pypoetry' \
    POETRY_HOME='/usr/local' 

COPY app /app
RUN poetry install --no-cache

EXPOSE 81
CMD ["poetry", "run", "fastapi", "run", "app/main.py", "--port", "81"]