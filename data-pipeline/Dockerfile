FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir requests google-cloud-storage

# Copy application code
COPY data-pipeline/ .

# Set entrypoint
ENTRYPOINT ["python", "main.py"]
