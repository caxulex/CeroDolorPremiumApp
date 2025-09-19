from __future__ import annotations

import os


def test_mistral_agent_offline_simulation(monkeypatch):
    # Force offline mode
    monkeypatch.setenv("USE_NETWORK", "false")
    if "MISTRAL_API_KEY" in os.environ:
        monkeypatch.delenv("MISTRAL_API_KEY", raising=False)
    from backend.src.agents.mistral_agent import MistralAgent

    agent = MistralAgent()
    res = agent.ask("Tengo dolor lumbar moderado por las mañanas")
    assert isinstance(res, dict)
    assert res.get("text")
    # Should keep minimal history
    assert len(agent.history) >= 2
