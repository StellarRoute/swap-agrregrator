# Chaos/degradation test (Phase 3 hardening): simulates a sustained signal-provider outage
# and a sustained Drips executor outage across several cycles, and verifies the system
# degrades to "no-action, logged" / "failed, logged, alerted" rather than crashing the loop.
import pytest
from celery.exceptions import TimeoutError as CeleryTimeoutError
from langgraph.checkpoint.memory import MemorySaver
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import core.orchestrator as orchestrator_module
from config.settings import Settings
from core.orchestrator import Orchestrator
from core.state import PathConfig
from db.models import AgentRunLog, Base
from workers.celery_app import celery_app


@pytest.fixture(autouse=True)
def _eager_celery():
    celery_app.conf.task_always_eager = True
    celery_app.conf.task_eager_propagates = True
    yield
    celery_app.conf.task_always_eager = False


@pytest.fixture
def _sqlite_session_factory(monkeypatch):
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    monkeypatch.setattr(orchestrator_module, "SessionFactory", factory)
    return factory


def _one_path():
    return [PathConfig(path_id="A-B", hops=["A", "B"], pool_ids=["pool-a-b"])]


def test_sustained_signal_outage_degrades_to_no_action(_sqlite_session_factory, monkeypatch):
    class _AlwaysTimeoutResult:
        def get(self, timeout=None):
            raise CeleryTimeoutError("simulated signal API outage")

    class _AlwaysTimeoutTask:
        def delay(self, *args, **kwargs):
            return _AlwaysTimeoutResult()

    monkeypatch.setattr(orchestrator_module, "ingest_signal_task", _AlwaysTimeoutTask())

    settings = Settings(_env_file=None)  # default threshold; depletion-only score stays low
    orchestrator = Orchestrator(_one_path(), settings, checkpointer=MemorySaver())

    for _ in range(3):
        orchestrator.run_cycle()  # must never raise despite the signal API being down

    with _sqlite_session_factory() as session:
        rows = session.query(AgentRunLog).order_by(AgentRunLog.created_at).all()
    assert len(rows) == 3
    assert all(row.decision_action == "no_act" for row in rows)
    assert all(row.execution_success for row in rows)  # "skip" is itself a successful no-op


def test_sustained_drips_outage_degrades_to_logged_failure_and_alerts(
    _sqlite_session_factory, monkeypatch
):
    class _AlwaysFailResult:
        def get(self, timeout=None):
            raise RuntimeError("simulated drips outage: max retries exceeded")

    class _AlwaysFailExecuteTask:
        def delay(self, *args, **kwargs):
            return _AlwaysFailResult()

    monkeypatch.setattr(orchestrator_module, "execute_drips_adjustment_task", _AlwaysFailExecuteTask())

    alerts = []
    monkeypatch.setattr(
        orchestrator_module.alert_sink,
        "alert",
        lambda title, detail, severity="warning": alerts.append((title, severity)),
    )

    # Threshold low enough that depletion alone (no signal contribution needed) forces "act"
    # deterministically, so every cycle reaches the executor regardless of mock signal randomness.
    settings = Settings(_env_file=None, risk_score_threshold=0.01, executor_failure_alert_threshold=3)
    orchestrator = Orchestrator(_one_path(), settings, checkpointer=MemorySaver())

    for _ in range(3):
        orchestrator.run_cycle()  # must never raise despite every Drips call failing

    with _sqlite_session_factory() as session:
        rows = session.query(AgentRunLog).order_by(AgentRunLog.created_at).all()
    assert len(rows) == 3
    assert all(row.decision_action == "act" for row in rows)
    assert all(not row.execution_success for row in rows)
    assert any(title == "repeated executor failures" and severity == "critical" for title, severity in alerts)
