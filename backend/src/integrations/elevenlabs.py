from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ElevenLabsConfig:
    api_key: str | None
    tts_voice_id: str | None = None
    stt_model: str = "conversational"
    tts_model: str = "eleven_turbo_v2"
    base_url: str | None = None  # allow custom endpoints


class ElevenLabsClient:
    """Minimal, env-guarded wrapper for ElevenLabs STT/TTS with offline simulation.

    Real calls are only made if ELEVENLABS_API_KEY is set and USE_NETWORK=true.
    Otherwise, methods return deterministic simulated outputs for tests.
    """

    def __init__(self, cfg: ElevenLabsConfig | None = None) -> None:
        api_key = os.getenv("ELEVENLABS_API_KEY")
        use_network = os.getenv("USE_NETWORK", "false").lower() == "true"
        tts_voice_id = os.getenv("ELEVENLABS_TTS_VOICE_ID")
        base_url = os.getenv("ELEVENLABS_BASE_URL")
        self.cfg = cfg or ElevenLabsConfig(api_key=api_key, tts_voice_id=tts_voice_id, base_url=base_url)
        self._use_network = use_network and bool(self.cfg.api_key)

    def transcribe(self, _audio_bytes: bytes, *, language: str = "es") -> dict[str, Any]:
        """Transcribe audio to text.

        Behavior:
        - Offline simulation (default): returns a deterministic Spanish transcript for tests.
        - Real API call: only attempted when both `ELEVENLABS_API_KEY` is set and `USE_NETWORK=true`.
        """
        if not self._use_network:
            # Simulate a stable transcript for tests
            return {"text": "simulado: registro de dolor", "language": language, "confidence": 0.99}
        # Placeholder for real API call (omitted intentionally); keep signature stable
        # Implement with requests if needed: POST /v1/transcriptions
        return {"error": "network_not_implemented"}

    def synthesize(self, _text: str, *, voice_id: str | None = None, language: str = "es") -> dict[str, Any]:
        """Synthesize speech from text.

        Behavior:
        - Offline simulation (default): returns a stubbed audio payload description.
        - Real API call: only attempted when both `ELEVENLABS_API_KEY` is set and `USE_NETWORK=true`.
        """
        if not self._use_network:
            # Simulate an audio payload (metadata only, not binary)
            return {"audio": "<simulado>", "voice_id": voice_id or (self.cfg.tts_voice_id or "default"), "language": language}
        # Placeholder for real API call (omitted intentionally)
        return {"error": "network_not_implemented"}
