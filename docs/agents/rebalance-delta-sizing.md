# Rebalance delta sizing

`decision_agent.decide()` chooses how much liquidity to move and which pool to target.

## Target pool

Selects the pool with the highest depletion ratio among risk inputs (`max(risk.inputs, key=depletion_ratio)`).

## Delta sizing

Uses available headroom and severity from `RiskAssessment` to scale `proposed_delta`. Low confidence or below-threshold scores yield `NO_ACTION` decisions.

## Severity interaction

Higher assessed risk increases proposed adjustment within configured max delta bounds.

See `agents/decision_agent.py` lines 43-61 and unit tests for numeric examples.
