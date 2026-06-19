# Celery queue routing

Tasks route to `ingestion` or `execution` queues via `task_routes` in `workers/celery_app.py`.

| Task name | Queue |
|-----------|-------|
| `stellarhydra.ingest_pool` | ingestion |
| `stellarhydra.ingest_signal` | ingestion |
| `stellarhydra.execute_drips_adjustment` | execution |

## Worker command

Docker Compose and Kubernetes worker deployments should subscribe to both:

```
celery -A workers.celery_app worker -Q ingestion,execution
```

Size concurrency per queue in production so ingestion polls are not starved by slow Drips executions.

See `docker-compose.yml` and `deploy/k8s/deployment-worker.yaml`.
