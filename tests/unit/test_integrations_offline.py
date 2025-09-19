from __future__ import annotations

from backend.src.integrations.aiml_api import AIMLClient
from backend.src.integrations.elevenlabs import ElevenLabsClient
from backend.src.integrations.mistral import MistralClient


def test_elevenlabs_offline_simulation(monkeypatch):
    monkeypatch.delenv("ELEVENLABS_API_KEY", raising=False)
    monkeypatch.setenv("USE_NETWORK", "false")
    client = ElevenLabsClient()
    t = client.transcribe(b"fake-bytes")
    s = client.synthesize("hola")
    assert "text" in t and t["text"].startswith("simulado")
    assert "audio" in s and s["audio"] == "<simulado>"


def test_mistral_offline_simulation(monkeypatch):
    monkeypatch.delenv("MISTRAL_API_KEY", raising=False)
    monkeypatch.setenv("USE_NETWORK", "false")
    client = MistralClient()
    r = client.chat([{ "role": "user", "content": "recomienda"}])
    e = client.extract("Tengo dolor en la espalda por las mañanas")
    assert r.get("choices") and "plan" in r["choices"][0]["message"]["content"]
    assert e.get("pain_location") == "espalda baja"


def test_aiml_offline_simulation(monkeypatch):
    monkeypatch.delenv("AIML_API_KEY", raising=False)
    monkeypatch.setenv("USE_NETWORK", "false")
    client = AIMLClient()
    sent = client.sentiment("Hoy me siento bien, casi sin dolor")
    pos = client.posture_hint(b"fake-bytes")
    assert sent.get("label") in {"positivo", "negativo", "neutral"}
    assert pos.get("finding")
