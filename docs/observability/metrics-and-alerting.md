# Metrics and alerting

## Prometheus

`GET /metrics` on admin API renders Prometheus text format via `render_prometheus_metrics()` in `core/observability.py`.

## Debug snapshot

`GET /debug/metrics` (authenticated) returns in-memory `metrics.snapshot()` for quick operator inspection.

## Structured metrics module

`core/observability.py` tracks cycle counts, execution outcomes, and timing (see code for metric names).

## Alerting

`core/alerting.py` triggers when executor failures exceed `EXECUTOR_FAILURE_ALERT_THRESHOLD`.

Configure webhook or PagerDuty integration in alerting module as deployment matures.

## Logging

Set `LOG_LEVEL` env var. Orchestrator and workers use standard Python logging.
