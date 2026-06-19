# Risk scoring heuristic

`predict_risk()` in `agents/prediction_agent.py` scores each hop and keeps the worst.

## Weights

| Component | Weight |
|-----------|--------|
| Reserve depletion ratio | 0.5 |
| Velocity score | 0.3 |
| Sentiment magnitude | 0.2 |

## Depletion

`_depletion_ratio` compares oldest vs newest `reserve_a` in pool history. Requires at least `MIN_HISTORY_POINTS` (2) snapshots or returns 0.

## Confidence penalties

Starts at 1.0, minus 0.4 if history too short, minus 0.4 if signal stale.

## Aggregation

Per-path risk uses the hop with the highest combined score; confidence tracks that hop.

See PRD open question #6 for future ML replacement.
