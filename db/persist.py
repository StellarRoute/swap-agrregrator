# Persist pool and signal snapshots for time-series prediction inputs.
from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from core.state import PoolSnapshot, SignalSnapshot
from db.models import PoolSnapshotRecord, SignalSnapshotRecord


def persist_pool_snapshot(session: Session, snapshot: PoolSnapshot) -> None:
    session.add(
        PoolSnapshotRecord(
            id=str(uuid.uuid4()),
            pool_id=snapshot.pool_id,
            reserve_a=snapshot.reserve_a,
            reserve_b=snapshot.reserve_b,
            volume_24h=snapshot.volume_24h,
        )
    )
    session.commit()


def persist_signal_snapshot(session: Session, signal: SignalSnapshot) -> None:
    session.add(
        SignalSnapshotRecord(
            id=str(uuid.uuid4()),
            asset=signal.asset,
            velocity_score=signal.velocity_score,
            sentiment_score=signal.sentiment_score,
            stale=signal.stale,
        )
    )
    session.commit()
