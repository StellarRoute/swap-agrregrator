# Centrally enforces hard risk limits (kill switch, per-cycle delta cap, per-path cooldown)
# independent of agent decision logic, per PRD feature F8.
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from config.settings import Settings
from core.kill_switch import kill_switch
from core.state import RebalanceDecision
from db.models import AgentRunLog


class RiskLimitEnforcer:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def authorize(self, decision: RebalanceDecision, session: Session) -> RebalanceDecision:
        if self._settings.kill_switch_engaged or kill_switch.engaged:
            return decision.model_copy(
                update={
                    "action": "no_act",
                    "proposed_delta": 0.0,
                    "reason": "blocked by kill switch (risk_limits)",
                }
            )

        if decision.action != "act":
            return decision

        cooldown_block = self._check_cooldown(decision, session)
        if cooldown_block is not None:
            return cooldown_block

        clamped_delta = min(decision.proposed_delta, self._settings.max_stream_delta_per_cycle)
        if clamped_delta != decision.proposed_delta:
            return decision.model_copy(update={"proposed_delta": clamped_delta})

        return decision

    def _check_cooldown(
        self, decision: RebalanceDecision, session: Session
    ) -> RebalanceDecision | None:
        last_act = session.execute(
            select(AgentRunLog)
            .where(
                AgentRunLog.path_id == decision.path_id,
                AgentRunLog.decision_action == "act",
                AgentRunLog.execution_success.is_(True),
            )
            .order_by(AgentRunLog.created_at.desc())
            .limit(1)
        ).scalar_one_or_none()

        if last_act is None:
            return None

        # created_at is stored as UTC (server_default=func.now()); some backends (e.g. SQLite)
        # return it naive, so tag it explicitly rather than risk a local-timezone conversion.
        created_at = last_act.created_at
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        elapsed = (datetime.now(timezone.utc) - created_at).total_seconds()
        if elapsed < self._settings.rebalance_cooldown_seconds:
            return decision.model_copy(
                update={
                    "action": "no_act",
                    "proposed_delta": 0.0,
                    "reason": (
                        f"blocked by cooldown ({elapsed:.0f}s < "
                        f"{self._settings.rebalance_cooldown_seconds}s since last rebalance)"
                    ),
                }
            )
        return None
