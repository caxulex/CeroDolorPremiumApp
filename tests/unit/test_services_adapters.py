from __future__ import annotations

from pathlib import Path

import pytest

from backend.src.services import aip_service, aiper_service, asd_service


def test_tts_speak_adapter_offline(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    monkeypatch.setenv("USE_ADAPTERS", "true")
    monkeypatch.delenv("ELEVENLABS_API_KEY", raising=False)
    out = aip_service.tts_speak("hola", voice=None)
    # With adapter offline, we return utf-8 bytes of a stubbed audio string
    assert isinstance(out, (bytes, type(None)))


def test_stt_transcribe_adapter_offline(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    monkeypatch.setenv("USE_ADAPTERS", "true")
    monkeypatch.delenv("ELEVENLABS_API_KEY", raising=False)
    # create empty file to simulate audio path
    audio = tmp_path / "a.wav"
    audio.write_bytes(b"")
    text = aip_service.stt_transcribe(str(audio))
    assert isinstance(text, str)


def test_asd_analyze_with_mistral_adapter_offline(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("USE_ADAPTERS", "true")
    monkeypatch.delenv("MISTRAL_API_KEY", raising=False)
    out = asd_service.analyze_data("p1", {"a": 1})
    assert isinstance(out, dict)
    assert "patterns_detected" in out


def test_aiper_generate_intervention_adapter_offline(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("USE_ADAPTERS", "true")
    monkeypatch.delenv("MISTRAL_API_KEY", raising=False)
    result = aiper_service.generate_intervention("p1")
    assert isinstance(result, str)
    assert len(result) > 0
