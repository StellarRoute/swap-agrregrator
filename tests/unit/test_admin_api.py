# Verifies the admin API's API-key gate and that the kill-switch endpoints actually
# toggle the shared runtime kill switch consulted by the decision agent and risk limits.
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import api.admin as admin_module
import config.settings as settings_module
from core.kill_switch import kill_switch
from db.models import Base


@pytest.fixture(autouse=True)
def _reset_kill_switch():
    yield
    kill_switch.disengage()


@pytest.fixture
def client(monkeypatch):
    settings_module.get_settings.cache_clear()
    monkeypatch.setenv("ADMIN_API_KEY", "test-key")
    settings_module.get_settings.cache_clear()

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    monkeypatch.setattr(admin_module, "SessionFactory", sessionmaker(bind=engine, expire_on_commit=False))

    yield TestClient(admin_module.app)
    settings_module.get_settings.cache_clear()


def test_protected_endpoint_without_key_is_rejected(client):
    response = client.get("/audit-log")
    assert response.status_code == 401


def test_protected_endpoint_with_correct_key_succeeds(client):
    response = client.get("/audit-log", headers={"x-api-key": "test-key"})
    assert response.status_code == 200
    assert response.json() == []


def test_healthz_and_metrics_require_no_key(client):
    assert client.get("/healthz").status_code == 200
    assert client.get("/metrics").status_code == 200


def test_kill_switch_endpoints_toggle_shared_kill_switch(client):
    assert kill_switch.engaged is False

    response = client.post("/kill-switch/engage", headers={"x-api-key": "test-key"})
    assert response.status_code == 200
    assert kill_switch.engaged is True

    response = client.post("/kill-switch/disengage", headers={"x-api-key": "test-key"})
    assert response.status_code == 200
    assert kill_switch.engaged is False
