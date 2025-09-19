import pytest
from backend.orchestrator_api.app import app
from fastapi.testclient import TestClient


client = TestClient(app)


def test_health_ok():
    r = client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    assert data["data"]["status"] == "ok"
