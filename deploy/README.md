# Deployment

## Staging

`docker-compose.yml` at the repo root is the staging-equivalent stack (Postgres, Redis,
orchestrator, worker, admin API) and is sufficient for staging today.

## Production (Kubernetes)

Manifests under `k8s/` assume a managed Postgres and managed Redis (RDS/Cloud SQL +
Elasticache/Memorystore or equivalent) rather than self-hosting stateful services in-cluster.
Apply in order:

```bash
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
# Create the real secret via your secrets manager — do NOT commit a filled-in secret.yaml.
# k8s/secret.yaml.example shows the required keys.
kubectl apply -f k8s/deployment-orchestrator.yaml
kubectl apply -f k8s/deployment-worker.yaml
kubectl apply -f k8s/deployment-admin-api.yaml
```

The image referenced (`ghcr.io/stellarroute/swap-agrregrator:latest`) is built and pushed by
the `build-and-push` CI job on every merge to `main` — see `.github/workflows/ci.yml`.

Run database migrations against the target environment before rolling out a new image:

```bash
DATABASE_URL=<target> alembic upgrade head
```
