# StellarHydra Runbook

## Engage the kill switch (stop all rebalancing immediately)

Preferred (no restart, takes effect on the next cycle):

```bash
curl -X POST https://<admin-api-host>/kill-switch/engage -H "x-api-key: $ADMIN_API_KEY"
```

This sets `core.kill_switch.kill_switch`, an in-process runtime flag checked independently
by both the decision agent and the risk-limit enforcer (defense in depth — either check
alone is sufficient to block execution). It resets to disengaged if the orchestrator
process restarts.

Fallback (durable across restarts, requires a redeploy/restart to take effect):
set `KILL_SWITCH_ENGAGED=true` in the environment/ConfigMap and restart the orchestrator.

To resume: `POST /kill-switch/disengage` with the same header.

Verify it took effect: `GET /debug/metrics` — `counters["orchestrator.decisions.no_act"]`
should be climbing and no new `act` decisions should appear in the audit log.

## Rotate a misbehaving signal provider

1. Confirm the problem: `GET /audit-log?path_id=<path>` and check `risk_inputs.<pool_id>.signal_stale`
   on recent rows, or watch the `stellarhydra_stale_signal_total{asset=...}` Prometheus counter.
2. If it's a transient outage, no action is needed — `HttpSignalProvider` degrades to a
   stale/neutral signal automatically (see `adapters/signal_adapter.py`), which lowers
   prediction confidence and the decision agent will not act on low-confidence input.
3. If the provider is sustained-bad (wrong values, not just down), flip
   `USE_MOCK_SIGNAL_PROVIDER=true` in the environment and restart the worker to fall back
   to the deterministic mock while the real provider issue is resolved.
4. Once a replacement provider is selected, implement it behind the existing
   `SignalProvider` interface (`adapters/signal_adapter.py`) — no agent or orchestrator
   code needs to change.

## Read the audit log for an incident

Every cycle, for every path, writes one row to `agent_run_log` (table) /
`GET /audit-log` (API), containing: the risk score and confidence that drove the
decision, the full per-pool `risk_inputs` (depletion ratio, velocity, sentiment, staleness,
history depth) that produced that score, the decision and its reason, and the execution
result. To investigate an incident:

```bash
curl "https://<admin-api-host>/audit-log?path_id=<path>&since=2026-06-19T00:00:00Z" \
  -H "x-api-key: $ADMIN_API_KEY"
```

Cross-reference `run_id` with orchestrator logs (structured JSON on stdout) for the same
run to see the raw exception, if any, that the row's `execution_detail` summarizes.

## Repeated executor failures

The orchestrator tracks consecutive Drips executor failures per path in-process and fires
a `critical`-severity alert (currently logged via `core.alerting.LoggingAlertSink`; wire a
real sink — e.g. Slack/PagerDuty — by implementing `AlertSink` once a webhook/integration
key is available) once `EXECUTOR_FAILURE_ALERT_THRESHOLD` (default 3) consecutive failures
occur on the same path. On alert: check `GET /audit-log?path_id=<path>` for the
`execution_detail` of recent rows, and check Drips Wave's own status/dashboard — most
executor failures are upstream API issues surfaced after the task's own retry/backoff
(`workers/tasks.py`) has been exhausted.
