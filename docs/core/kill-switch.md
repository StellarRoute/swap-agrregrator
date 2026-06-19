# Kill switch

Module: `core/kill_switch.py`

## Purpose

Immediately stop all drip executions when engaged. Prediction and audit continue; graph routes to `skip` after decide.

## Startup

`KILL_SWITCH_ENGAGED` env var sets initial state (default `false`).

## Admin API

| Endpoint | Auth | Effect |
|----------|------|--------|
| `POST /kill-switch/engage` | `x-api-key` | Engage switch |
| `POST /kill-switch/disengage` | `x-api-key` | Disengage |

See [api/admin-api.md](../api/admin-api.md).

## Runbook

Documented in root [RUNBOOK.md](../../RUNBOOK.md) for incident response.

## Testing

`tests/unit/test_admin_api.py` covers engage/disengage with API key.
