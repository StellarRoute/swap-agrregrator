# Structured (JSON) logging setup, in-process metrics, and audit-log queries for PRD feature F9.
from __future__ import annotations

import json
import logging
import sys
import time
from collections import defaultdict, deque
from datetime import datetime
from threading import Lock

from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, generate_latest
from sqlalchemy import select
from sqlalchemy.orm import Session

from db.models import AgentRunLog

PROMETHEUS_CONTENT_TYPE = CONTENT_TYPE_LATEST

decisions_total = Counter(
    "stellarhydra_decisions_total", "Agent decisions by action", ["action"]
)
executor_failures_total = Counter(
    "stellarhydra_executor_failures_total", "Drips executor failures"
)
stale_signal_total = Counter(
    "stellarhydra_stale_signal_total", "Stale or failed signal ingestions", ["asset"]
)
kill_switch_engaged_gauge = Gauge(
    "stellarhydra_kill_switch_engaged", "1 if either kill switch is currently engaged"
)


def render_prometheus_metrics() -> bytes:
    return generate_latest()


class _JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": time.time(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload)


def configure_logging(level: str = "INFO") -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(_JsonFormatter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


class Metrics:
    """In-process counters and recent-decision ring buffer; Phase 3 wires this to a real exporter."""

    def __init__(self, max_recent: int = 100) -> None:
        self._lock = Lock()
        self._counters: dict[str, int] = defaultdict(int)
        self._recent_decisions: deque = deque(maxlen=max_recent)

    def increment(self, name: str, amount: int = 1) -> None:
        with self._lock:
            self._counters[name] += amount

    def record_decision(self, path_id: str, action: str, risk_score: float) -> None:
        with self._lock:
            self._recent_decisions.append(
                {"path_id": path_id, "action": action, "risk_score": risk_score, "ts": time.time()}
            )

    def snapshot(self) -> dict:
        with self._lock:
            return {
                "counters": dict(self._counters),
                "recent_decisions": list(self._recent_decisions),
            }


metrics = Metrics()


def query_audit_log(
    session: Session,
    path_id: str | None = None,
    run_id: str | None = None,
    since: float | None = None,
    limit: int = 100,
) -> list[AgentRunLog]:
    """Lets an operator trace any executed action back to its triggering inputs (F9)."""
    stmt = select(AgentRunLog)
    if path_id:
        stmt = stmt.where(AgentRunLog.path_id == path_id)
    if run_id:
        stmt = stmt.where(AgentRunLog.run_id == run_id)
    if since:
        stmt = stmt.where(AgentRunLog.created_at >= datetime.fromtimestamp(since))
    stmt = stmt.order_by(AgentRunLog.created_at.desc()).limit(limit)
    return list(session.execute(stmt).scalars().all())
