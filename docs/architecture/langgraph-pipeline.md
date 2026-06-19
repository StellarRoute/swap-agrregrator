# LangGraph pipeline

Defined in `core/graph.py` function `build_graph()`.

## Nodes

| Node | Function | Description |
|------|----------|-------------|
| `ingest_pool` | Load pool history | Calls `PoolStateProvider.get_pool_history` per pool ID on path |
| `ingest_signal` | Load signals | `SignalProvider.get_signal` per hop destination asset |
| `predict` | `predict_risk` | Agent computes risk score and confidence |
| `decide` | `decide` | Applies thresholds, kill switch, cooldown |
| `execute` | Drips adjust | `drips_client.adjust_stream(pool_id, delta)` |
| `skip` | No-op | Below threshold, low confidence, or kill switch |

## Routing

After `decide`, conditional edge routes to `execute` when `decision.action == "act"`, else `skip`.

## State

Typed as `GraphState` in `core/state.py` (path, pool history, signals, decision, execution result).

## Providers injected at build time

`build_graph(pool_provider, signal_provider, drips_client, settings)` keeps graph pure for unit tests with fakes.
