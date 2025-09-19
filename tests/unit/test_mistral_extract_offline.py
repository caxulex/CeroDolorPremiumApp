from __future__ import annotations

import os


def test_mistral_extract_offline(monkeypatch):
    monkeypatch.setenv("USE_NETWORK", "false")
    if "MISTRAL_API_KEY" in os.environ:
        monkeypatch.delenv("MISTRAL_API_KEY", raising=False)
    from backend.src.integrations.mistral import MistralClient

    client = MistralClient()
    res = client.extract("Dolor lumbar al despertar, intensidad 5.")
    assert isinstance(res, dict)
    # Offline stub contains expected keys
    assert res.get("pain_location") == "espalda baja"
    assert isinstance(res.get("intensity"), int)
