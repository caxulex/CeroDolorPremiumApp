import pytest
from fastapi.testclient import TestClient
from backend.orchestrator_api.app import app


client = TestClient(app)


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    from backend.orchestrator_api import config as cfg
    monkeypatch.setattr(cfg.settings, "use_network", False, raising=False)


def test_clinician_flow_happy_path(monkeypatch):
    class DummyClient:
        async def invoke_agent(self, agent_id, payload):
            if "investigator" in agent_id:
                return {"risks": []}
            if "clinician_report" in agent_id:
                return {"summary": "OK"}
            return "Guidance"

    class DummySolana:
        async def anchor_hash(self, h):
            return "FAKE_SIG_ABC"

    monkeypatch.setattr("backend.orchestrator_api.flows.proyecto_b.MistralClient", lambda: DummyClient())
    monkeypatch.setattr("backend.orchestrator_api.flows.proyecto_b.SolanaService", lambda: DummySolana())

    payload = {
        "patient_id": "p1",
        "clinician_id": "c1",
        "scope": "last_7_days",
        "require_blockchain_anchor": True,
    }
    r = client.post("/proyecto-b/clinician", json=payload)
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert body["data"]["anchor_tx"] == "FAKE_SIG_ABC"


def test_researcher_flow_happy_path(monkeypatch):
    class DummyClient:
        async def invoke_agent(self, agent_id, payload):
            return {"insights": 3}

    class DummySolana:
        async def anchor_hash(self, h):
            return "FAKE_SIG_DEF"

    monkeypatch.setattr("backend.orchestrator_api.flows.proyecto_b.MistralClient", lambda: DummyClient())
    monkeypatch.setattr("backend.orchestrator_api.flows.proyecto_b.SolanaService", lambda: DummySolana())

    payload = {
        "study_id": "s1",
        "criteria": {"patient_id": "p1"},
        "anonymization_level": "safe-default",
        "require_blockchain_anchor": True,
    }
    r = client.post("/proyecto-b/researcher", json=payload)
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert body["data"]["anchor_tx"] == "FAKE_SIG_DEF"
