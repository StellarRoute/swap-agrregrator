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


class WebhookAlertSink(AlertSink):
    def __init__(self, webhook_url: str) -> None:
        self._webhook_url = webhook_url

    def alert(self, title: str, detail: str, severity: str = "warning") -> None:
        try:
            import httpx

            httpx.post(
                self._webhook_url,
                json={"title": title, "detail": detail, "severity": severity},
                timeout=5.0,
            ).raise_for_status()
        except Exception as exc:  # noqa: BLE001
            logger.warning("Webhook alert failed: %s", exc)


def build_alert_sink(webhook_url: str | None = None) -> AlertSink:
    if webhook_url:
        return WebhookAlertSink(webhook_url)
    return LoggingAlertSink()


alert_sink: AlertSink = LoggingAlertSink()
