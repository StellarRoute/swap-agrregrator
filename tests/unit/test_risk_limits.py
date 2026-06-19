# Verifies risk limit enforcement is independent of agent output: kill switch always
# blocks, deltas are clamped to the configured max, and cooldown blocks a too-soon repeat.
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config.settings import Settings
from core.risk_limits import RiskLimitEnforcer
from core.state import RebalanceDecision
from db.models import AgentRunLog, Base


def _session_factory():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)


def _decision(delta=500.0):
    return RebalanceDecision(
        path_id="A-B", action="act", proposed_delta=delta, target_pool_id="pool-a-b", reason="test"
    )


def test_kill_switch_overrides_agent_decision():
    settings = Settings(_env_file=None, kill_switch_engaged=True)
    enforcer = RiskLimitEnforcer(settings)
    factory = _session_factory()
    with factory() as session:
        result = enforcer.authorize(_decision(), session)
    assert result.action == "no_act"


def test_delta_clamped_to_configured_max():
    settings = Settings(_env_file=None, max_stream_delta_per_cycle=100.0)
    enforcer = RiskLimitEnforcer(settings)
    factory = _session_factory()
    with factory() as session:
        result = enforcer.authorize(_decision(delta=500.0), session)
    assert result.action == "act"
    assert result.proposed_delta == 25.0


def test_delta_respects_max_stream_before_capital_pct():
    settings = Settings(
        _env_file=None,
        max_stream_delta_per_cycle=1000.0,
        max_path_capital_pct=0.1,
    )
    enforcer = RiskLimitEnforcer(settings)
    factory = _session_factory()
    with factory() as session:
        result = enforcer.authorize(_decision(delta=500.0), session)
    assert result.proposed_delta == 100.0


def test_no_act_decision_passes_through_unchanged():
    settings = Settings(_env_file=None)
    enforcer = RiskLimitEnforcer(settings)
    factory = _session_factory()
    no_act = RebalanceDecision(
        path_id="A-B", action="no_act", proposed_delta=0.0, target_pool_id=None, reason="below threshold"
    )
    with factory() as session:
        result = enforcer.authorize(no_act, session)
    assert result == no_act


def test_cooldown_blocks_too_soon_repeat_rebalance():
    settings = Settings(_env_file=None, rebalance_cooldown_seconds=300)
    enforcer = RiskLimitEnforcer(settings)
    factory = _session_factory()
    with factory() as session:
        session.add(
            AgentRunLog(
                run_id="prev",
                path_id="A-B",
                risk_score=0.9,
                confidence=1.0,
                risk_inputs={},
                decision_action="act",
                decision_reason="prior cycle",
                proposed_delta=200.0,
                target_pool_id="pool-a-b",
                execution_success=True,
                execution_detail="ok",
            )
        )
        session.commit()

        result = enforcer.authorize(_decision(), session)

    assert result.action == "no_act"
    assert "cooldown" in result.reason
