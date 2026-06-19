# Kubernetes deployment

Manifests: `deploy/k8s/`

## Apply order

```bash
kubectl apply -f deploy/k8s/namespace.yaml
kubectl apply -f deploy/k8s/configmap.yaml
# Create secret from secret.yaml.example keys — do not commit real values
kubectl apply -f deploy/k8s/deployment-orchestrator.yaml
kubectl apply -f deploy/k8s/deployment-worker.yaml
kubectl apply -f deploy/k8s/deployment-admin-api.yaml
```

## Stateful services

Use managed Postgres and Redis (RDS, Cloud SQL, ElastiCache, Memorystore). Do not run database pods in production without ops ownership.

## Image

CI builds and pushes `ghcr.io/stellarroute/swap-agrregrator:latest` on merge to `main` (see `.github/workflows/ci.yml`).

## Migrations

Before rollout:

```bash
DATABASE_URL=<target> alembic upgrade head
```

## Staging

Root `docker-compose.yml` provides a staging-equivalent stack locally (see `deploy/README.md`).
