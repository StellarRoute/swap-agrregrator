# Alert triggers

`core/alerting.py` defines `AlertSink`; default `LoggingAlertSink` writes warnings or errors to the `stellarhydra.alerts` logger.

## Orchestrator triggers

| Event | Severity | Title |
|-------|----------|-------|
| Stale signal after ingest timeout | warning | stale signal source |
| Consecutive executor failures | critical | drips executor degraded |
| Kill switch engaged at cycle start | critical | kill switch engaged |

## Swapping sinks

Implement `AlertSink.alert(title, detail, severity)` and assign `alert_sink` for Slack/PagerDuty webhooks.

See `core/orchestrator.py` (`ingest_signal_node`, `execute_node`, `run_cycle`).
