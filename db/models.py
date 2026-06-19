# SQLAlchemy ORM models for pool/signal snapshot history and the agent run audit log.
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Float, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class PoolSnapshotRecord(Base):
    __tablename__ = "pool_snapshots"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    pool_id: Mapped[str] = mapped_column(String, index=True)
    reserve_a: Mapped[float] = mapped_column(Float)
    reserve_b: Mapped[float] = mapped_column(Float)
    volume_24h: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )


class SignalSnapshotRecord(Base):
    __tablename__ = "signal_snapshots"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    asset: Mapped[str] = mapped_column(String, index=True)
    velocity_score: Mapped[float] = mapped_column(Float)
    sentiment_score: Mapped[float] = mapped_column(Float)
    stale: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )


class AgentRunLog(Base):
    """Audit trail (PRD F9): every prediction/decision/execution, traceable by path/time/run_id."""

    __tablename__ = "agent_run_log"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    run_id: Mapped[str] = mapped_column(String, index=True)
    path_id: Mapped[str] = mapped_column(String, index=True)
    risk_score: Mapped[float] = mapped_column(Float)
    confidence: Mapped[float] = mapped_column(Float)
    risk_inputs: Mapped[dict] = mapped_column(JSON)
    decision_action: Mapped[str] = mapped_column(String)
    decision_reason: Mapped[str] = mapped_column(String)
    proposed_delta: Mapped[float] = mapped_column(Float)
    target_pool_id: Mapped[str | None] = mapped_column(String, nullable=True)
    execution_success: Mapped[bool] = mapped_column(Boolean)
    execution_detail: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
