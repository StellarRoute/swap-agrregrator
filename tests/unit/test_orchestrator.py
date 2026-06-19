# Verifies the orchestrator runs multiple paths per cycle, persists an audit log row per
# path, and isolates one path's failure from the others. Uses Celery's eager mode and an
# injected in-memory LangGraph checkpointer so no live Redis/Postgres is required.
import pytest
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


def _paths():
    return [
        PathConfig(path_id="A-B", hops=["A", "B"], pool_ids=["pool-a-b"]),
        PathConfig(path_id="C-D", hops=["C", "D"], pool_ids=["pool-c-d"]),
    ]


def test_run_cycle_persists_one_audit_row_per_path(_sqlite_session_factory):
    # Threshold near 1.0 keeps the outcome deterministic regardless of the mock signal
    # provider's randomized velocity/sentiment values for this cycle.
    settings = Settings(_env_file=None, risk_score_threshold=0.99)
    orchestrator = Orchestrator(_paths(), settings, checkpointer=MemorySaver())

    orchestrator.run_cycle()

    with _sqlite_session_factory() as session:
        rows = session.query(AgentRunLog).all()
    assert {row.path_id for row in rows} == {"A-B", "C-D"}


def test_run_cycle_continues_after_one_path_fails(_sqlite_session_factory, monkeypatch):
    """The first path's pool ingestion fails outright; the second path must still complete
    and get persisted, proving one bad cycle can't take down the whole orchestration loop."""
    from workers.tasks import ingest_pool_task as real_ingest_pool_task

    call_count = {"n": 0}

    class _FailFirstCallResult:
        def get(self, timeout=None):
            raise RuntimeError("simulated ingestion failure")

    class _FlakyIngestPoolTask:
        def delay(self, *args, **kwargs):
            call_count["n"] += 1
            if call_count["n"] == 1:
                return _FailFirstCallResult()
            return real_ingest_pool_task.delay(*args, **kwargs)

    monkeypatch.setattr(orchestrator_module, "ingest_pool_task", _FlakyIngestPoolTask())

    settings = Settings(_env_file=None, risk_score_threshold=0.99)
    orchestrator = Orchestrator(_paths(), settings, checkpointer=MemorySaver())

    orchestrator.run_cycle()  # must not raise despite the first path's ingestion failing

    with _sqlite_session_factory() as session:
        rows = session.query(AgentRunLog).all()
    assert len(rows) == 1
