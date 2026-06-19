# Unit tests for snapshot persistence helpers.
from unittest.mock import MagicMock

from core.state import PoolSnapshot, SignalSnapshot
from db.persist import persist_pool_snapshot, persist_signal_snapshot


def test_persist_pool_snapshot_adds_record():
    session = MagicMock()
    snapshot = PoolSnapshot(pool_id="pool-1", reserve_a=100.0, reserve_b=200.0, volume_24h=5000.0)

    persist_pool_snapshot(session, snapshot)

    session.add.assert_called_once()
    session.commit.assert_called_once()


def test_persist_signal_snapshot_adds_record():
    session = MagicMock()
    signal = SignalSnapshot(asset="XLM", velocity_score=0.5, sentiment_score=-0.1, stale=False)

    persist_signal_snapshot(session, signal)

    session.add.assert_called_once()
    session.commit.assert_called_once()
