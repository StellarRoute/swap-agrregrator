# Risk limits

Implementation: `core/risk_limits.py` and decision agent checks.

## Settings (env)

| Variable | Role |
|----------|------|
| `RISK_SCORE_THRESHOLD` | Do not act below this score |
| `MAX_STREAM_DELTA_PER_CYCLE` | Upper bound on drip adjustment magnitude |
| `MAX_PATH_CAPITAL_PCT` | Limit fraction of path capital at risk |
| `REBALANCE_COOLDOWN_SECONDS` | Minimum time between actions on same path |

## Decision outcomes

When limits block action, decision agent sets `action` to skip with human-readable `decision_reason` stored in audit log.

## Testing

`tests/unit/test_risk_limits.py` covers boundary conditions.

## Operations

Tune thresholds per environment via ConfigMap in Kubernetes (`deploy/k8s/configmap.yaml`) without code changes.
