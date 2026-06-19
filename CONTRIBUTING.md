# Contributing to swap-agrregrator

LangGraph multi-agent system for Stellar DEX liquidity prediction and Drips stream rebalancing (StellarHydra ALB codebase).

## Setup

```bash
git clone https://github.com/StellarRoute/swap-agrregrator.git
cd swap-agrregrator
cp .env.example .env
pip install -e ".[dev]"
docker-compose up -d
pytest -q
```

## Layout

| Path | Role |
|------|------|
| `core/graph.py` | LangGraph StateGraph wiring |
| `agents/` | Prediction and decision agents |
| `adapters/` | Drips, signals, Soroban pool providers |
| `api/admin.py` | Operator admin FastAPI |
| `workers/` | Celery ingestion and execution |
| `db/` | SQLAlchemy models and Alembic migrations |

## Pull requests

- Target branch: `main`
- Keep mock adapters enabled unless testing real sandbox APIs
- Run `pytest -q` before pushing
- Read [PRD.md](PRD.md) open questions before changing adapter contracts

## Documentation

Add guides under `docs/`. Cross-link from [docs/README.md](docs/README.md).
