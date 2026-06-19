# Orchestrator timeout degradation

Queued ingest nodes tolerate slow or failed Celery workers.

## task_timeout

```python
max(pool_poll_interval_seconds, signal_poll_interval_seconds, 10)
```

## ingest_pool_node

On `CeleryTimeoutError`, logs a warning and sets `pool_history[pool_id] = []` for that pool.

## ingest_signal_node

On timeout, creates `SignalSnapshot` with `stale=True`, increments `stale_signal_total`, and calls `alert_sink.alert`.

Prediction confidence penalties then reflect missing data instead of crashing the cycle.

See `core/orchestrator.py`.
