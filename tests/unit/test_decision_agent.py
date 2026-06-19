# Verifies decision thresholding respects risk threshold, confidence floor, and kill switch.
from agents.decision_agent import decide
from config.settings import Settings
from core.state import PathConfig, RiskAssessment


def _make_state(risk_score, confidence=1.0):
    path = PathConfig(path_id="A-B", hops=["A", "B"], pool_ids=["pool-a-b"])
    risk = RiskAssessment(
        path_id="A-B",
        risk_score=risk_score,
        confidence=confidence,
        inputs={"pool-a-b": {"depletion_ratio": risk_score}},
    )
    return {"path": path, "risk_assessment": risk, "decision": None}


def test_below_threshold_results_in_no_act():
    settings = Settings(_env_file=None, risk_score_threshold=0.65)
    state = decide(_make_state(0.3), settings)
    assert state["decision"].action == "no_act"


def test_above_threshold_results_in_act_within_limits():
    settings = Settings(_env_file=None, risk_score_threshold=0.65, max_stream_delta_per_cycle=1000)
    state = decide(_make_state(0.9), settings)
    decision = state["decision"]
    assert decision.action == "act"
    assert 0 < decision.proposed_delta <= settings.max_stream_delta_per_cycle


def test_kill_switch_blocks_action_even_above_threshold():
    settings = Settings(_env_file=None, risk_score_threshold=0.65, kill_switch_engaged=True)
    state = decide(_make_state(0.95), settings)
    assert state["decision"].action == "no_act"
    assert "kill switch" in state["decision"].reason


def test_low_confidence_blocks_action_even_above_threshold():
    settings = Settings(_env_file=None, risk_score_threshold=0.65)
    state = decide(_make_state(0.9, confidence=0.2), settings)
    assert state["decision"].action == "no_act"
