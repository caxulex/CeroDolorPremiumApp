import pytest
from fastapi.testclient import TestClient
from backend.orchestrator_api.app import app


client = TestClient(app)


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    # Ensure settings.use_network is False to avoid real calls
    from backend.orchestrator_api import config as cfg
    monkeypatch.setattr(cfg.settings, "use_network", False, raising=False)


def test_checkin_flow_happy_path(monkeypatch):
    # Mock Mistral agent responses in sequence
    class DummyClient:
        def __init__(self):
            self.calls = []

        async def invoke_agent(self, agent_id, payload):
            self.calls.append((agent_id, payload))
            if "investigator" in agent_id:
                return {"analysis": "ok"}
            if "patient_ui" in agent_id:
                return "Mensaje empatico"
            return {"intervention": "do breathing"}

    from backend.orchestrator_api import flows
    # Patch constructors used in route
    monkeypatch.setattr("backend.orchestrator_api.flows.proyecto_a.MistralClient", lambda: DummyClient())
    monkeypatch.setattr("backend.orchestrator_api.flows.proyecto_a.ElevenLabsClient", lambda: None)

    payload = {
        "patient_id": "p1",
        "pain_level": 5,
        "description": "dolor moderado",
        "use_tts": False,
    }
    r = client.post("/proyecto-a/checkin", json=payload)
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert "summary" in body["data"]
    assert body["data"]["audio_b64"] is None
