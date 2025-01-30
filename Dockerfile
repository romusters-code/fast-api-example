FROM python:3.12.6-slim-bookworm

WORKDIR /app

# Adding a package such as 'curl' allows better caching of this layer
RUN apt-get update && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir certifi==2024.12.14 pip==25.0 poetry==2.0.1  --trusted-host pypi.org --trusted-host files.pythonhosted.org

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

RUN poetry install --no-cache

COPY app /app

# Be careful: this should not run in docker compose environment. It is only used to circumvent corporate proxy for personal projects.
ENV PYTHONHTTPSVERIFY=0 
# If there are certificates, add them.
RUN cat /app/certificates.crt >> /usr/local/lib/python3.12/site-packages/certifi/cacert.pem

EXPOSE 8080
CMD ["poetry", "run", "fastapi", "run", "main.py", "--port", "8080"]