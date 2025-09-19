import os

import pytest

USE_NETWORK = os.getenv("USE_NETWORK") == "true"
HAS_ELEVEN = bool(os.getenv("ELEVENLABS_API_KEY"))
HAS_MISTRAL = bool(os.getenv("MISTRAL_API_KEY"))

network_required = pytest.mark.skipif(
    not USE_NETWORK or (not HAS_ELEVEN and not HAS_MISTRAL),
    reason="Network mode and at least one API key required"
)


@network_required
def test_mistral_chat_minimal():
    if not HAS_MISTRAL:
        pytest.skip("MISTRAL_API_KEY missing")
    from backend.src.integrations.mistral import MistralClient  # type: ignore
    client = MistralClient()
    out = client.chat([{"role": "user", "content": "Hola"}])
    assert isinstance(out, dict)
    assert "choices" in out or "offline" in out.get("mode", "")


@network_required
def test_elevenlabs_tts_minimal(tmp_path):
    if not HAS_ELEVEN:
        pytest.skip("ELEVENLABS_API_KEY missing")
    from backend.src.integrations.elevenlabs import ElevenLabsClient  # type: ignore
    client = ElevenLabsClient()
    synth = client.synthesize("Hola mundo de prueba", voice_id="Rachel")
    assert isinstance(synth, dict)
    # Real returns audio_b64, offline returns audio
    assert ("audio" in synth) or ("audio_b64" in synth)
