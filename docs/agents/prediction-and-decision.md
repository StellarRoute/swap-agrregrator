# Prediction and decision agents

## Prediction (`agents/prediction_agent.py`)

`predict_risk(state)` consumes:

- `path` - target swap path with pool IDs and hop assets
- `pool_history` - time series from pool provider
- `signals` - sentiment/market data per asset

Outputs risk score and confidence on state for the decision agent.

## Decision (`agents/decision_agent.py`)

`decide(state, settings)` evaluates:

- `RISK_SCORE_THRESHOLD` - minimum score to act
- `MAX_STREAM_DELTA_PER_CYCLE` - cap proposed drip delta
- `MAX_PATH_CAPITAL_PCT` - limit capital exposure
- `REBALANCE_COOLDOWN_SECONDS` - throttle repeat actions
- Kill switch state from `core/kill_switch.py`

Returns `decision` with `action` (`act` or `skip`), `proposed_delta`, `target_pool_id`, and reason string.

## Testing

- `tests/unit/test_prediction_agent.py`
- `tests/unit/test_decision_agent.py`
- `tests/unit/test_chaos_degradation.py` for failure modes
