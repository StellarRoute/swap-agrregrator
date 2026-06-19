# Unimplemented risk settings

Some settings exist in configuration but are not enforced in code yet.

## MAX_PATH_CAPITAL_PCT

`Settings.max_path_capital_pct` appears in `config/settings.py` and Kubernetes ConfigMap examples.

`RiskLimitEnforcer` and `decision_agent` do **not** read this value when authorizing deltas.

Document deployments accordingly: lowering the env var alone will not cap capital until enforcement lands.

Track implementation in issues referencing PRD capital limits.

See `core/risk_limits.py` and `agents/decision_agent.py`.
