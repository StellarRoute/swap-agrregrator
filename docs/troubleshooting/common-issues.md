# Troubleshooting

## run_once fails immediately

- Confirm `pip install -e ".[dev]"` completed
- Check Python 3.11+
- With mock adapters, external APIs are not required

## Orchestrator cannot connect to Postgres

- `docker-compose up -d` running
- `DATABASE_URL` matches compose credentials
- Run `alembic upgrade head`

## Celery worker idle

- Verify broker URL matches Redis container
- Check worker logs for import errors

## Admin API 503 on protected routes

Set `ADMIN_API_KEY` in environment before starting uvicorn.

## All executions skip

- Check kill switch: `GET /debug/metrics` or env `KILL_SWITCH_ENGAGED`
- Risk score may be below `RISK_SCORE_THRESHOLD`
- Cooldown may block repeat actions

## Soroban adapter NotImplementedError

Expected until `STELLARROUTE_CONTRACT_ID` ABI is confirmed (PRD OQ3). Mock pool provider used in tests.

## Live Drips errors

Set `USE_MOCK_DRIPS_CLIENT=false` only after validating HTTP contract against Drips sandbox.
