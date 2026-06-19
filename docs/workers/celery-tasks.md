# Celery workers

## App

`workers/celery_app.py` defines the Celery application instance.

## Tasks

`workers/tasks.py` decouples long-running ingestion and execution from the orchestrator tick. Tasks call into adapters and persist audit rows.

## Start worker

```bash
celery -A workers.celery_app worker --loglevel=INFO
```

## Broker

Uses `CELERY_BROKER_URL` and `CELERY_RESULT_BACKEND` from settings (Redis by default in `docker-compose.yml`).

## Docker Compose

Root `docker-compose.yml` includes worker and orchestrator services for staging-style stacks.

## Kubernetes

Separate deployment manifest: `deploy/k8s/deployment-worker.yaml`
