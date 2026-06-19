# State models reference

Typed dicts and Pydantic models in `core/state.py` define orchestrator wire data.

## PathConfig

- `path_id`: stable string identifier
- `hops`: ordered asset codes
- `pool_ids`: same length as hops minus one (one pool per hop)

## GraphState keys

Includes `path`, `pool_history`, `signals`, `risk_assessment`, `decision`, `execution_result`.

## Snapshots

`PoolSnapshot`: reserves, volume, timestamp per pool.

`SignalSnapshot`: `velocity_score`, `sentiment_score`, `stale` flag per asset.

## ExecutionResult

`success` bool plus `detail` string from Drips executor task.

Use this file when mapping API or admin responses to graph state.
