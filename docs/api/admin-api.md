# Admin API

App: `api/admin.py` (FastAPI)

## Start

```bash
uvicorn api.admin:app --host 0.0.0.0 --port 8000
```

Set `ADMIN_API_KEY` before starting.

## Public endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/healthz` | Liveness |
| GET | `/metrics` | Prometheus exposition |

## Authenticated (`x-api-key` header)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/debug/metrics` | In-memory metrics snapshot |
| GET | `/audit-log` | Query audit rows (filters: path_id, run_id, since, limit) |
| POST | `/kill-switch/engage` | Stop executions |
| POST | `/kill-switch/disengage` | Resume executions |

## Audit log response fields

Includes `run_id`, `path_id`, `risk_score`, `confidence`, `decision_action`, `decision_reason`, `proposed_delta`, `target_pool_id`, `execution_success`, `execution_detail`, `created_at`.

## Security note

Single shared API key is suitable for internal/VPN admin surfaces only. Do not expose publicly without stronger auth.
