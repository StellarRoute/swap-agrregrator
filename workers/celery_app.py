# Celery application instance shared by all task modules; broker/backend come from settings.
from __future__ import annotations

from celery import Celery

from config.settings import get_settings

_settings = get_settings()

celery_app = Celery(
    "stellarhydra",
    broker=_settings.celery_broker_url,
    backend=_settings.celery_result_backend,
    include=["workers.tasks"],
)
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_track_started=True,
    # Ingestion (frequent, latency-sensitive) and execution (rarer, can tolerate queueing
    # behind retries) are routed to separate queues so a backlog in one doesn't starve the
    # other; size worker concurrency per queue independently in deployment (see deploy/).
    task_routes={
        "stellarhydra.ingest_pool": {"queue": "ingestion"},
        "stellarhydra.ingest_signal": {"queue": "ingestion"},
        "stellarhydra.execute_drips_adjustment": {"queue": "execution"},
    },
)
