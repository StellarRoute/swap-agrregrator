# Builds the StellarHydra app/worker image; orchestrator and Celery workers share this image, differing only by CMD.
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
RUN pip install --no-cache-dir -e ".[dev]"

COPY . .

CMD ["python", "scripts/run_once.py"]
