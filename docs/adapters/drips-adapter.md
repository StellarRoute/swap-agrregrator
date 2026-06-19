# Drips adapter

File: `adapters/drips_adapter.py`

## Interface

`DripsClient.adjust_stream(target_pool_id, proposed_delta) -> ExecutionResult`

## Implementations

| Class | When used |
|-------|-----------|
| Mock client | `USE_MOCK_DRIPS_CLIENT=true` (default) |
| `HttpDripsClient` | Live sandbox/production |

## Configuration

- `DRIPS_API_BASE_URL`
- `DRIPS_API_KEY`
- `DRIPS_ACCOUNT_ID`
- `USE_MOCK_DRIPS_CLIENT`

## Contract assumptions

HTTP client uses best-effort request shape documented in code comments. Confirm against Drips Wave sandbox before setting `USE_MOCK_DRIPS_CLIENT=false` (PRD open question).

## Failures

Executor failures increment observability counters. After `EXECUTOR_FAILURE_ALERT_THRESHOLD`, alerting hooks in `core/alerting.py` fire (see observability docs).
