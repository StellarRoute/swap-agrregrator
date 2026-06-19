# enforce_limits node

Phase 2 inserts a dedicated risk gate between decision and execution.

## Placement

Graph edges: `decide` → `enforce_limits` → `execute` (when decision is actionable).

## Implementation

`enforce_limits_node` calls `RiskLimitEnforcer.authorize(decision, session)` with a SQLAlchemy session. The enforcer may downgrade or block proposals that violate persisted limits.

## vs decision_agent

`decision_agent.decide()` proposes deltas from heuristics. `enforce_limits` is the centralized policy enforcement point (PRD F8).

See `core/orchestrator.py` and `core/risk_limits.py`.
