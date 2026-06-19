# SQLAlchemy engine/session setup shared by the orchestrator, risk limits, and observability queries.
from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from config.settings import get_settings

_settings = get_settings()
engine = create_engine(_settings.database_url, pool_pre_ping=True)
SessionFactory: sessionmaker[Session] = sessionmaker(bind=engine, expire_on_commit=False)


def session_scope() -> Session:
    return SessionFactory()
