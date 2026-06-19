# Thresholds path risk scores against configured limits and emits an act/no-act decision.
from __future__ import annotations

from config.settings import Settings
from core.kill_switch import kill_switch
from core.state import GraphState, RebalanceDecision

MIN_CONFIDENCE = 0.5


def decide(state: GraphState, settings: Settings) -> GraphState:
    path = state["path"]
    risk = state["risk_assessment"]

    if risk is None:
        raise ValueError("decide() called before predict_risk() populated risk_assessment")

    # Two independent kill switches: a static deploy-time default (settings) and a
    # runtime-toggleable one an operator can flip via the admin API (core.kill_switch).
    if settings.kill_switch_engaged or kill_switch.engaged:
        state["decision"] = RebalanceDecision(
            path_id=path.path_id,
            action="no_act",
            proposed_delta=0.0,
            target_pool_id=None,
            reason="kill switch engaged",
        )
        return state

    if risk.risk_score < settings.risk_score_threshold or risk.confidence < MIN_CONFIDENCE:
        state["decision"] = RebalanceDecision(
            path_id=path.path_id,
            action="no_act",
            proposed_delta=0.0,
            target_pool_id=None,
            reason=(
                f"risk_score={risk.risk_score:.2f} confidence={risk.confidence:.2f} "
                f"below threshold={settings.risk_score_threshold:.2f}"
            ),
        )
        return state

    # The hop with the highest reserve depletion becomes the rebalancing target;
    # delta scales with how far the score is over threshold, capped at the configured max.
    target_pool_id = max(risk.inputs, key=lambda pool_id: risk.inputs[pool_id]["depletion_ratio"])
    headroom = max(1e-6, 1.0 - settings.risk_score_threshold)
    severity = (risk.risk_score - settings.risk_score_threshold) / headroom
    proposed_delta = min(
        settings.max_stream_delta_per_cycle,
        settings.max_stream_delta_per_cycle * max(0.1, severity),
    )

    state["decision"] = RebalanceDecision(
        path_id=path.path_id,
        action="act",
        proposed_delta=proposed_delta,
        target_pool_id=target_pool_id,
        reason=(
            f"risk_score={risk.risk_score:.2f} exceeded threshold="
            f"{settings.risk_score_threshold:.2f}"
        ),
    )
    return state
