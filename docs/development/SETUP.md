# Local development setup

## Prerequisites

- Python 3.11+
- Docker Compose (Postgres + Redis)

## Install

```bash
cp .env.example .env
pip install -e ".[dev]"
docker-compose up -d
```

## Phase 1: single cycle

```bash
python scripts/run_once.py
```

Runs one LangGraph path through ingest, predict, decide, and execute (mock adapters by default).

## Phase 2: orchestrator + worker

```bash
alembic upgrade head
celery -A workers.celery_app worker --loglevel=INFO &
python scripts/run_orchestrator.py
```

## Phase 3: admin API

```bash
export ADMIN_API_KEY=some-local-dev-key
uvicorn api.admin:app --reload
```

Public: `GET /healthz`, `GET /metrics`. Protected: audit log, debug metrics, kill switch.

## Mock adapters

Default `.env.example` sets:

- `USE_MOCK_DRIPS_CLIENT=true`
- `USE_MOCK_SIGNAL_PROVIDER=true`

Safe for local dev without external API keys.
