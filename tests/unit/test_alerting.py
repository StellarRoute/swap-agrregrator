# Tests for webhook alert sink and readyz endpoint.
from unittest.mock import MagicMock, patch

from core.alerting import WebhookAlertSink, build_alert_sink


def test_build_alert_sink_prefers_webhook():
    sink = build_alert_sink("https://hooks.example/alerts")
    assert isinstance(sink, WebhookAlertSink)


def test_webhook_alert_sink_posts_payload():
    sink = WebhookAlertSink("https://hooks.example/alerts")
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    with patch("httpx.post", return_value=mock_response) as mock_post:
        sink.alert("stale signals", "no fresh data for 5m", severity="critical")
    mock_post.assert_called_once()
    assert mock_post.call_args.kwargs["json"]["severity"] == "critical"
