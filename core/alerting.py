# Minimal alerting interface. Ships with a logging-only sink since no real alerting
# webhook/credentials (Slack, PagerDuty, etc.) have been provided. Swapping in a real sink
# requires only a new AlertSink implementation — callers depend on the interface alone.
from __future__ import annotations

import logging
from abc import ABC, abstractmethod

logger = logging.getLogger("stellarhydra.alerts")


class AlertSink(ABC):
    @abstractmethod
    def alert(self, title: str, detail: str, severity: str = "warning") -> None:
        """Emit an alert. severity is "warning" or "critical"."""


class LoggingAlertSink(AlertSink):
    def alert(self, title: str, detail: str, severity: str = "warning") -> None:
        log_fn = logger.error if severity == "critical" else logger.warning
        log_fn("ALERT[%s]: %s — %s", severity, title, detail)


alert_sink: AlertSink = LoggingAlertSink()
