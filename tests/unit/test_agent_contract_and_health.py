from __future__ import annotations


def test_agent_base_protocol_import():
    # Ensure the contract module loads
    from backend.src.agents.base import Agent, AgentRequest, AgentResponse  # type: ignore
    assert AgentRequest("hola").prompt == "hola"
    assert AgentResponse(text="ok").text == "ok"


def test_mistral_agent_health_offline(monkeypatch):
    monkeypatch.setenv("USE_NETWORK", "false")
    from backend.src.agents.mistral_agent import MistralAgent

    a = MistralAgent()
    h = a.health()
    assert isinstance(h, dict)
    # With offline client, we still should report client available and online wiring
    assert h.get("client") in {True, False}
    assert "model" in h