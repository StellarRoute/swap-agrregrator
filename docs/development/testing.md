# Testing guide

## Run all tests

```bash
pytest -q
```

## Unit test layout

| File | Coverage |
|------|----------|
| `tests/unit/test_graph.py` | LangGraph routing |
| `tests/unit/test_prediction_agent.py` | Risk prediction |
| `tests/unit/test_decision_agent.py` | Policy decisions |
| `tests/unit/test_risk_limits.py` | Limit enforcement |
| `tests/unit/test_orchestrator.py` | Orchestrator loop |
| `tests/unit/test_admin_api.py` | Admin API and kill switch |
| `tests/unit/test_settings.py` | Config loading |
| `tests/unit/test_chaos_degradation.py` | Failure degradation |

## CI

`.github/workflows/ci.yml` runs pytest on push/PR to `main`.

## Writing tests

- Inject mock adapters; do not require live Drips or Postgres for unit tests
- Use in-memory or test database for integration tests when added
