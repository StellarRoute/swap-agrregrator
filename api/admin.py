# Minimal operator-facing admin API (Phase 3 hardening): view the audit log, view metrics,
# and engage/disengage the runtime kill switch. Everything except /metrics and /healthz is
# gated behind a single API key header — adequate for an internal/VPN-only admin surface,
# not a substitute for real user authn/authz if this is ever exposed more broadly.
from __future__ import annotations

from datetime import datetime

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Response

from config.settings import get_settings
from core.kill_switch import kill_switch
from core.kill_switch_redis import RedisKillSwitch
from core.observability import PROMETHEUS_CONTENT_TYPE, metrics, query_audit_log, render_prometheus_metrics
from db.session import SessionFactory
from sqlalchemy import text

app = FastAPI(title="StellarHydra Admin API")


def require_api_key(x_api_key: str = Header(default="")) -> None:
    settings = get_settings()
    if not settings.admin_api_key:
        raise HTTPException(status_code=503, detail="ADMIN_API_KEY is not configured")
    if x_api_key != settings.admin_api_key:
        raise HTTPException(status_code=401, detail="invalid or missing API key")


@app.get("/healthz")
def healthz() -> dict:
    return {"status": "ok"}


@app.get("/readyz")
def readyz() -> dict:
    try:
        with SessionFactory() as session:
            session.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False
    settings = get_settings()
    return {
        "ready": db_ok and bool(settings.admin_api_key),
        "database": db_ok,
        "admin_key_configured": bool(settings.admin_api_key),
    }


@app.get("/metrics")
def prometheus_metrics() -> Response:
    return Response(content=render_prometheus_metrics(), media_type=PROMETHEUS_CONTENT_TYPE)


@app.get("/debug/metrics", dependencies=[Depends(require_api_key)])
def debug_metrics() -> dict:
    return metrics.snapshot()


@app.get("/audit-log", dependencies=[Depends(require_api_key)])
def get_audit_log(
    path_id: str | None = None,
    run_id: str | None = None,
    since: datetime | None = Query(default=None),
    limit: int = 100,
) -> list[dict]:
    with SessionFactory() as session:
        rows = query_audit_log(
            session,
            path_id=path_id,
            run_id=run_id,
            since=since.timestamp() if since else None,
            limit=limit,
        )
        return [
            {
                "run_id": row.run_id,
                "path_id": row.path_id,
                "risk_score": row.risk_score,
                "confidence": row.confidence,
                "risk_inputs": row.risk_inputs,
                "decision_action": row.decision_action,
                "decision_reason": row.decision_reason,
                "proposed_delta": row.proposed_delta,
                "target_pool_id": row.target_pool_id,
                "execution_success": row.execution_success,
                "execution_detail": row.execution_detail,
                "created_at": row.created_at.isoformat(),
            }
            for row in rows
        ]


@app.post("/kill-switch/engage", dependencies=[Depends(require_api_key)])
def engage_kill_switch() -> dict:
    kill_switch.engage()
    try:
        RedisKillSwitch().engage()
    except Exception:
        pass
    return {"engaged": True}


@app.post("/kill-switch/disengage", dependencies=[Depends(require_api_key)])
def disengage_kill_switch() -> dict:
    kill_switch.disengage()
    try:
        RedisKillSwitch().disengage()
    except Exception:
        pass
    return {"engaged": False}
