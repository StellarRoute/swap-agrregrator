# Typed data models shared across agents, adapters, and the LangGraph state for one cycle.
from __future__ import annotations

import time
from typing import Literal, TypedDict

from pydantic import BaseModel, Field


class PathConfig(BaseModel):
    path_id: str
    hops: list[str]  # asset codes in hop order, e.g. ["XLM", "USDC", "yXLM"]
    pool_ids: list[str]  # one pool id per hop, len(pool_ids) == len(hops) - 1


class PoolSnapshot(BaseModel):
    pool_id: str
    reserve_a: float
    reserve_b: float
    volume_24h: float
    timestamp: float = Field(default_factory=time.time)


class SignalSnapshot(BaseModel):
    asset: str
    velocity_score: float  # momentum, roughly -1..1
    sentiment_score: float  # sentiment, roughly -1..1
    stale: bool = False
    timestamp: float = Field(default_factory=time.time)


class RiskAssessment(BaseModel):
    path_id: str
    risk_score: float
    confidence: float
    inputs: dict  # per-pool inputs that produced the score, kept for audit (F9)
    timestamp: float = Field(default_factory=time.time)


class RebalanceDecision(BaseModel):
    path_id: str
    action: Literal["act", "no_act"]
    proposed_delta: float
    target_pool_id: str | None
    reason: str
    timestamp: float = Field(default_factory=time.time)


class ExecutionResult(BaseModel):
    success: bool
    detail: str
    timestamp: float = Field(default_factory=time.time)


class GraphState(TypedDict, total=False):
    run_id: str
    path: PathConfig
    pool_history: dict[str, list[PoolSnapshot]]
    signals: dict[str, SignalSnapshot]
    risk_assessment: RiskAssessment | None
    decision: RebalanceDecision | None
    execution_result: ExecutionResult | None
