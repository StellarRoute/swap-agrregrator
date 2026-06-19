# MIN_CONFIDENCE gate

Separate from `RISK_SCORE_THRESHOLD` env configuration.

## Constant

```python
MIN_CONFIDENCE = 0.5  # decision_agent.py
```

## Behavior

Even when risk score exceeds the threshold, decisions below 0.5 confidence become `NO_ACTION` with rationale citing low confidence.

## Not env-configurable

Unlike `RISK_SCORE_THRESHOLD`, this gate is hardcoded. Change requires code edit and test update until settings expose it.

See `agents/decision_agent.py`.
