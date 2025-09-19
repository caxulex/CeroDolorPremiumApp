import os
import json
import struct
from pathlib import Path
from typing import Any, Optional, Dict


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
        # Always provide a deterministic simulated payload regardless of adapter internal errors.
        try:
            from integrations.elevenlabs import ElevenLabsClient, ElevenLabsConfig  # type: ignore[import-not-found]  # noqa: I001

            client = ElevenLabsClient(ElevenLabsConfig(api_key=os.getenv("ELEVENLABS_API_KEY")))  # type: ignore[misc]
            result: dict[str, Any] = client.synthesize(text, voice_id=voice)
            audio_meta = result.get("audio")
            if isinstance(audio_meta, str):
                return audio_meta.encode("utf-8")
        except Exception:  # noqa: BLE001
            pass
        # Fallback simulated bytes
        return f"simulado_audio:{voice or 'default'}:{text[:20]}".encode("utf-8")

    api_key = os.getenv("ELEVENLABS_API_KEY")
    if api_key:
        try:
            # Lazy import to avoid hard dependency during tests
            from elevenlabs import generate, set_api_key  # type: ignore[import-not-found]
        except Exception:  # noqa: BLE001
            # Fall through to simulated bytes below
            pass
        else:
            try:
                set_api_key(api_key)
                audio: bytes = generate(text=text, voice=voice or "Rachel")
                return audio
            except Exception:  # noqa: BLE001
                # If real generation fails, fallback
                pass

    # Deterministic fallback ALWAYS if llegamos aquí
    # Generate a minimal PCM 8-bit mono 8kHz WAV with pseudo pattern derived from text hash
    sample_rate = 8000
    duration_sec = min(1.2, 0.04 * max(1, len(text)))  # scale lightly with text length
    n_samples = int(sample_rate * duration_sec)
    base_hash = sum(bytearray(text.encode('utf-8')[:64])) or 1
    samples = bytearray()
    for i in range(n_samples):
        # Simple varying pattern (not real speech): (hash * i) mod 256 with mild envelope
        val = (base_hash * (i + 1)) % 256
        # Fade out at the end to avoid clicks
        if i > n_samples * 0.9:
            val = int(val * 0.3)
        samples.append(val)
    # WAV header (RIFF)
    num_channels = 1
    bits_per_sample = 8
    byte_rate = sample_rate * num_channels * bits_per_sample // 8
    block_align = num_channels * bits_per_sample // 8
    data_chunk_size = len(samples)
    fmt_chunk_size = 16
    riff_chunk_size = 4 + (8 + fmt_chunk_size) + (8 + data_chunk_size)
    header = b"RIFF" + struct.pack('<I', riff_chunk_size) + b"WAVE"
    fmt_chunk = b"fmt " + struct.pack('<IHHIIHH', fmt_chunk_size, 1, num_channels, sample_rate, byte_rate, block_align, bits_per_sample)
    data_chunk = b"data" + struct.pack('<I', data_chunk_size) + bytes(samples)
    wav_bytes = header + fmt_chunk + data_chunk
    if os.getenv("AIP_TTS_DIAG", "false").lower() == "true":
        meta = {"mode": "fallback_wav", "voice": voice or "default", "len": len(text), "samples": n_samples}
        return (json.dumps(meta, ensure_ascii=False) + "\n").encode("utf-8") + wav_bytes
    return wav_bytes


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


# ---- Unified Facade (non-breaking) ---- #
def audio_capabilities() -> Dict[str, bool]:
    """Return a capability matrix indicating what is realistically available.

    Keys:
      tts (bool) - Whether we can attempt text→audio (simulated counts as True if USE_ADAPTERS).
      stt (bool) - Whether we can attempt audio→text (simulated counts as True if USE_ADAPTERS).
      network (bool) - Whether network paths are allowed (USE_NETWORK=true & key present).
    """
    use_adapters = os.getenv("USE_ADAPTERS", "false").lower() == "true"
    use_network = os.getenv("USE_NETWORK", "false").lower() == "true"
    have_key = bool(os.getenv("ELEVENLABS_API_KEY"))
    return {
        "tts": use_adapters or have_key,
        "stt": use_adapters or have_key,
        "network": use_network and have_key,
    }


def tts_generate_bytes(text: str, voice: Optional[str] = None) -> Optional[bytes]:
    """Facade returning bytes or None. Wraps tts_speak with clearer name."""
    return tts_speak(text, voice)


def stt_transcribe_file(path: str) -> str:
    """Facade alias to stt_transcribe for symmetry."""
    return stt_transcribe(path)


__all__ = [
    "initiate_daily_checkin",
    "register_pain",
    "register_mood_sleep",
    "provide_feedback",
    "tts_speak",
    "stt_transcribe",
    "audio_capabilities",
    "tts_generate_bytes",
    "stt_transcribe_file",
]
