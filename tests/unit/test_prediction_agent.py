# Verifies bottleneck risk scoring responds correctly to reserve depletion and signal inputs.
from agents.prediction_agent import predict_risk
from core.state import PathConfig, PoolSnapshot, SignalSnapshot


def _make_state(history, signal):
    path = PathConfig(path_id="A-B", hops=["A", "B"], pool_ids=["pool-a-b"])
    return {
        "path": path,
        "pool_history": {"pool-a-b": history},
        "signals": {"B": signal} if signal else {},
        "risk_assessment": None,
        "decision": None,
        "execution_result": None,
    }


def test_depleted_reserves_with_rising_demand_score_high():
    history = [
        PoolSnapshot(
            pool_id="pool-a-b", reserve_a=100_000, reserve_b=100_000, volume_24h=10_000, timestamp=0
        ),
        PoolSnapshot(
            pool_id="pool-a-b", reserve_a=40_000, reserve_b=160_000, volume_24h=80_000, timestamp=30
        ),
    ]
    signal = SignalSnapshot(asset="B", velocity_score=0.9, sentiment_score=0.8, stale=False)
    state = _make_state(history, signal)

    result = predict_risk(state)

    assert result["risk_assessment"].risk_score > 0.6
    assert result["risk_assessment"].confidence == 1.0


def test_stable_reserves_with_flat_signal_score_low():
    history = [
        PoolSnapshot(
            pool_id="pool-a-b", reserve_a=100_000, reserve_b=100_000, volume_24h=10_000, timestamp=0
        ),
        PoolSnapshot(
            pool_id="pool-a-b", reserve_a=99_500, reserve_b=100_500, volume_24h=10_200, timestamp=30
        ),
    ]
    signal = SignalSnapshot(asset="B", velocity_score=-0.2, sentiment_score=0.05, stale=False)
    state = _make_state(history, signal)

    result = predict_risk(state)

    assert result["risk_assessment"].risk_score < 0.2


def test_missing_signal_reduces_confidence():
    history = [
        PoolSnapshot(
            pool_id="pool-a-b", reserve_a=100_000, reserve_b=100_000, volume_24h=10_000, timestamp=0
        ),
        PoolSnapshot(
            pool_id="pool-a-b", reserve_a=90_000, reserve_b=110_000, volume_24h=20_000, timestamp=30
        ),
    ]
    state = _make_state(history, signal=None)

    result = predict_risk(state)

    assert result["risk_assessment"].confidence < 1.0
