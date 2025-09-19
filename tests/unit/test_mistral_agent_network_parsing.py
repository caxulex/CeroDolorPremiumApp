from __future__ import annotations

from typing import Any


def test_mistral_agent_parses_network_response(monkeypatch):
    # Force network allowed and set a fake key so agent constructs client
    monkeypatch.setenv("USE_NETWORK", "true")
    monkeypatch.setenv("MISTRAL_API_KEY", "fake_key")

    # Import classes
    from backend.src.agents.mistral_agent import MistralAgent, MistralAgentConfig

    # Replace underlying client with a stub that returns a realistic payload
    class _StubClient:
        def chat(self, _messages: list[dict[str, str]], *_args: Any, **_kwargs: Any):
            return {
                "id": "chat-123",
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": "Respira 4-6 y una caminata suave de 10 minutos.",
                        }
                    }
                ],
            }

    agent = MistralAgent(MistralAgentConfig())
    # Inject stub
    agent._client = _StubClient()  # type: ignore[attr-defined]

    res = agent.ask("Contexto demo")
    assert isinstance(res, dict)
    assert res.get("text")
    assert "Respira" in res["text"] or "caminata" in res["text"]
    # History should have user + assistant turns appended
    assert len(agent.history) >= 2
