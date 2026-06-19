# StellarHydra — Agentic Liquidity Balancer (ALB)

A LangGraph-based multi-agent system that predicts bottlenecks on Stellar DEX multi-hop swap paths and proactively rebalances LP liquidity via Drips continuous funding streams, so the routes StellarRoute recommends are already well-funded when traders query them.

See [PRD.md](./PRD.md) for the full product spec and [ROADMAP.md](./ROADMAP.md) for the phased build plan.

## Local Setup

```bash
cp .env.example .env       # fill in real values where available; mock flags default to true
pip install -e ".[dev]"
docker-compose up
```

## Running a single end-to-end cycle (Phase 1)

```bash
python scripts/run_once.py
```

## Running the continuous multi-path orchestrator (Phase 2)

Requires Postgres and Redis (see `docker-compose.yml`) and a running Celery worker:

```bash
alembic upgrade head                                   # create db schema
celery -A workers.celery_app worker --loglevel=INFO &   # start the task queue worker
python scripts/run_orchestrator.py                      # start the recurring loop
```

## Running the admin API (Phase 3)

```bash
export ADMIN_API_KEY=some-local-dev-key
uvicorn api.admin:app --reload
```

`GET /audit-log`, `GET /debug/metrics`, and `POST /kill-switch/{engage,disengage}` require
the `x-api-key` header. `GET /metrics` (Prometheus exposition format) and `GET /healthz`
do not. See [RUNBOOK.md](./RUNBOOK.md) for operator procedures.

## Running tests

```bash
pytest -q
```

## Project Structure

```
agents/      LangGraph node implementations (prediction, decision)
adapters/    Integration boundaries: Soroban RPC, Drips API, signal providers (real + mock)
core/        Graph state, LangGraph wiring, orchestration loop, risk limits, observability,
             alerting, runtime kill switch
api/         Operator admin API (audit log, metrics, kill switch)
workers/     Celery app and tasks (ingestion, execution) decoupled from the orchestration tick
db/          SQLAlchemy models, session factory, and Alembic migrations
config/      Typed settings loaded from environment
deploy/      Kubernetes manifests and deployment notes
scripts/     CLI entrypoints
tests/       Unit tests
```

## Status

Mock adapters (`USE_MOCK_DRIPS_CLIENT`, `USE_MOCK_SIGNAL_PROVIDER`) are enabled by default until the Drips testnet integration shape and a concrete sentiment/market-data provider are confirmed — see PRD Open Questions. Real implementations exist behind the same interfaces (`adapters/drips_adapter.py:HttpDripsClient`, `adapters/signal_adapter.py:HttpSignalProvider`) with documented, best-effort assumptions about each API's contract — flip the `USE_MOCK_*` flags once real sandbox/API access confirms those contracts. The Soroban contract reader (`adapters/soroban_adapter.py:SorobanPoolStateProvider`) still raises `NotImplementedError` pending a confirmed StellarRoute contract ABI (Open Question #3); everything else runs end-to-end today.
