from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Dict
import json
import base64

import requests


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
            return {"text": "simulado: registro de dolor", "language": language, "confidence": 0.99}
        # Real call (basic; adjust endpoint/model as needed)
        try:
            base = self.cfg.base_url or "https://api.elevenlabs.io"
            url = f"{base.rstrip('/')}/v1/transcriptions"
            headers = {"xi-api-key": self.cfg.api_key or "", "Accept": "application/json"}
            files = {
                "file": ("audio.wav", _audio_bytes, "application/octet-stream"),
                "model": (None, self.cfg.stt_model),
                "language": (None, language),
            }
            resp = requests.post(url, headers=headers, files=files, timeout=30)
            if resp.status_code >= 400:
                return {"error": "http_error", "status": resp.status_code, "text": resp.text[:500]}
            data = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {"raw": resp.text[:500]}
            # Normalize expected keys
            text = data.get("text") or data.get("transcription") or ""
            return {"text": text, "language": language, "confidence": data.get("confidence")}
        except Exception as e:  # noqa: BLE001
            return {"error": "exception", "reason": str(e)}

    def synthesize(self, _text: str, *, voice_id: str | None = None, language: str = "es") -> dict[str, Any]:
        """Synthesize speech from text.

        Behavior:
        - Offline simulation (default): returns a stubbed audio payload description.
        - Real API call: only attempted when both `ELEVENLABS_API_KEY` is set and `USE_NETWORK=true`.
        """
        if not self._use_network:
            return {"audio": "<simulado>", "voice_id": voice_id or (self.cfg.tts_voice_id or "default"), "language": language}
        try:
            base = self.cfg.base_url or "https://api.elevenlabs.io"
            url = f"{base.rstrip('/')}/v1/text-to-speech/{voice_id or (self.cfg.tts_voice_id or 'Rachel')}"
            headers = {
                "xi-api-key": self.cfg.api_key or "",
                "Accept": "application/json",
                "Content-Type": "application/json",
            }
            payload: Dict[str, Any] = {
                "text": _text,
                "model_id": self.cfg.tts_model,
                "voice_settings": {"stability": 0.5, "similarity_boost": 0.5},
            }
            resp = requests.post(url, headers=headers, data=json.dumps(payload), timeout=60)
            if resp.status_code >= 400:
                return {"error": "http_error", "status": resp.status_code, "text": resp.text[:500]}
            # ElevenLabs returns audio bytes; we base64 them for JSON safety
            b64 = base64.b64encode(resp.content).decode("ascii")
            return {"audio_b64": b64, "voice_id": voice_id or (self.cfg.tts_voice_id or "default"), "language": language}
        except Exception as e:  # noqa: BLE001
            return {"error": "exception", "reason": str(e)}
