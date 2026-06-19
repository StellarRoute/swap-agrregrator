# Architecture overview

swap-agrregrator implements the Agentic Liquidity Balancer: predict path risk, decide Drips adjustments, execute under policy caps.

## High-level flow

```
Orchestrator tick / run_once
    -> LangGraph (pool ingest -> signal ingest -> predict -> decide -> execute|skip)
    -> Drips adapter (mock or HTTP)
    -> Postgres audit log
```

## Processes

| Process | Entry | Purpose |
|---------|-------|---------|
| `scripts/run_once.py` | CLI | Single-path demo (Phase 1) |
| `scripts/run_orchestrator.py` | CLI | Recurring multi-path loop (Phase 2) |
| Celery worker | `workers/celery_app.py` | Async ingestion/execution |
| Admin API | `api/admin.py` | Audit, metrics, kill switch |

## Adapters

| Adapter | File | Status |
|---------|------|--------|
| Drips | `adapters/drips_adapter.py` | HTTP + mock |
| Signals | `adapters/signal_adapter.py` | HTTP + mock |
| Soroban pools | `adapters/soroban_adapter.py` | NotImplemented pending ABI |

## Related repos

- [StellarRoute](https://github.com/StellarRoute/StellarRoute) - authoritative router
- [StellarHydra](https://github.com/StellarRoute/StellarHydra) - companion Python ALB (parallel evolution)
