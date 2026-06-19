# Docker Compose local stack

`docker-compose.yml` runs five services for full Phase 2 dev.

| Service | Role |
|---------|------|
| postgres | Agent audit DB, migrations |
| redis | Celery broker |
| app | `python scripts/run_orchestrator.py` |
| worker | Celery worker with `-Q ingestion,execution` |
| api | Optional admin HTTP (if defined in compose tail) |

## Healthchecks

Postgres uses `pg_isready`; Redis uses `redis-cli ping`. App and worker wait for both.

## Volumes

`postgres_data` persists local DB across restarts.

Copy `.env.example` to `.env` before `docker compose up`.

See root `Dockerfile` for the shared image build.
