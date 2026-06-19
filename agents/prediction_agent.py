# Heuristic bottleneck-risk scoring: combines on-chain pool reserve trend with external
# market velocity + sentiment signals into a single 0-1 risk score per path.
from __future__ import annotations

from core.state import GraphState, PoolSnapshot, RiskAssessment, SignalSnapshot

# Initial heuristic weights (PRD assumes rules-based scoring for V1 — see PRD Open
# Question #6). Tune once real signal data distributions are known.
WEIGHT_RESERVE_DEPLETION = 0.5
WEIGHT_VELOCITY = 0.3
WEIGHT_SENTIMENT_MAGNITUDE = 0.2

MIN_HISTORY_POINTS = 2


def _depletion_ratio(history: list[PoolSnapshot]) -> float:
    if len(history) < MIN_HISTORY_POINTS:
        return 0.0
    oldest, newest = history[0], history[-1]
    if oldest.reserve_a <= 0:
        return 0.0
    ratio = (oldest.reserve_a - newest.reserve_a) / oldest.reserve_a
    return max(0.0, min(1.0, ratio))


def _signal_components(signal: SignalSnapshot | None) -> tuple[float, float]:
    if signal is None:
        return 0.0, 0.0
    velocity = max(0.0, signal.velocity_score)  # only rising demand adds risk
    sentiment_magnitude = abs(signal.sentiment_score)
    return velocity, sentiment_magnitude


def predict_risk(state: GraphState) -> GraphState:
    path = state["path"]
    pool_history = state.get("pool_history", {})
    signals = state.get("signals", {})

    worst_score = 0.0
    worst_confidence = 1.0
    inputs: dict = {}

    for hop_index, pool_id in enumerate(path.pool_ids):
        history = pool_history.get(pool_id, [])
        depletion = _depletion_ratio(history)

        # Risk on a hop is driven by demand flowing into the hop's destination asset.
        asset = path.hops[hop_index + 1]
        signal = signals.get(asset)
        velocity, sentiment_magnitude = _signal_components(signal)

        score = (
            WEIGHT_RESERVE_DEPLETION * depletion
            + WEIGHT_VELOCITY * velocity
            + WEIGHT_SENTIMENT_MAGNITUDE * sentiment_magnitude
        )
        score = max(0.0, min(1.0, score))

        has_min_history = len(history) >= MIN_HISTORY_POINTS
        is_stale = signal.stale if signal else True
        confidence = 1.0
        if not has_min_history:
            confidence -= 0.4
        if is_stale:
            confidence -= 0.4
        confidence = max(0.0, min(1.0, confidence))

        inputs[pool_id] = {
            "depletion_ratio": depletion,
            "velocity": velocity,
            "sentiment_magnitude": sentiment_magnitude,
            "signal_stale": is_stale,
            "history_points": len(history),
        }

        if score >= worst_score:
            worst_score = score
            worst_confidence = confidence

    state["risk_assessment"] = RiskAssessment(
        path_id=path.path_id,
        risk_score=worst_score,
        confidence=worst_confidence,
        inputs=inputs,
    )
    return state
