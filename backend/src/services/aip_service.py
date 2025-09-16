import os
from pathlib import Path
from typing import Any


def initiate_daily_checkin(patient_id: str) -> str:
    _ = patient_id
    return "Daily check-in initiated."

def register_pain(patient_id: str, level: int, description: str):
    return {"patient_id": patient_id, "level": level, "description": description}

def register_mood_sleep(patient_id: str, mood: str, sleep: str):
    return {"patient_id": patient_id, "mood": mood, "sleep": sleep}

def provide_feedback(patient_id: str, context: str) -> str:
    _ = (patient_id, context)
    return "Empathetic feedback provided."


def tts_speak(text: str, voice: str | None = None) -> bytes | None:
    """Synthesize speech from text using ElevenLabs if configured; else fallback.

    Returns raw audio bytes (if available) or None when falling back.
    """
    # Prefer adapter-based path when requested
    use_adapters = os.getenv("USE_ADAPTERS", "false").lower() == "true"
    if use_adapters:
        try:
            # Local import to keep optional dependency and avoid import ordering issues
            from integrations.elevenlabs import ElevenLabsClient, ElevenLabsConfig  # type: ignore[import-not-found]  # noqa: I001

            client = ElevenLabsClient(ElevenLabsConfig(api_key=os.getenv("ELEVENLABS_API_KEY")))  # type: ignore[misc]
            result: dict[str, Any] = client.synthesize(text, voice_id=voice)
            audio_meta = result.get("audio")
            if isinstance(audio_meta, str):
                return audio_meta.encode("utf-8")
        except Exception:  # noqa: BLE001
            return None

    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        # Fallback: no audio produced
        return None
    try:
        # Lazy import to avoid hard dependency during tests
        from elevenlabs import generate, set_api_key  # type: ignore[import-not-found]
    except Exception:  # noqa: BLE001
        return None
    else:
        set_api_key(api_key)
        audio: bytes = generate(text=text, voice=voice or "Rachel")
        return audio


def stt_transcribe(audio_path: str) -> str:
    """Transcribe audio to text using ElevenLabs if configured; else fallback.

    Placeholder implementation returns an empty string to remain deterministic.
    """
    use_adapters = os.getenv("USE_ADAPTERS", "false").lower() == "true"
    if use_adapters:
        try:
            from integrations.elevenlabs import ElevenLabsClient, ElevenLabsConfig  # type: ignore[import-not-found]  # noqa: I001

            client = ElevenLabsClient(ElevenLabsConfig(api_key=os.getenv("ELEVENLABS_API_KEY")))  # type: ignore[misc]
            audio_bytes: bytes = b""
            try:
                with Path(audio_path).open("rb") as fh:
                    audio_bytes = fh.read()
            except Exception:  # noqa: BLE001
                audio_bytes = b""
            result = client.transcribe(audio_bytes)
            text = result.get("text") if isinstance(result, dict) else None
            return text if isinstance(text, str) else ""
        except Exception:  # noqa: BLE001
            return ""

    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        return ""
    # Real implementation intentionally omitted (network-free placeholder)
    return ""
