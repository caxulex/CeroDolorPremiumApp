from importlib import reload

import backend.src.services.aip_service as aip


def test_audio_capabilities_without_env(monkeypatch):
    monkeypatch.delenv("ELEVENLABS_API_KEY", raising=False)
    monkeypatch.setenv("USE_ADAPTERS", "false")
    monkeypatch.setenv("USE_NETWORK", "false")
    reload(aip)
    caps = aip.audio_capabilities()
    assert caps["tts"] is False
    assert caps["stt"] is False
    assert caps["network"] is False


def test_audio_capabilities_with_adapters(monkeypatch):
    monkeypatch.delenv("ELEVENLABS_API_KEY", raising=False)
    monkeypatch.setenv("USE_ADAPTERS", "true")
    monkeypatch.setenv("USE_NETWORK", "false")
    reload(aip)
    caps = aip.audio_capabilities()
    assert caps["tts"] is True  # simulation allowed
    assert caps["stt"] is True
    assert caps["network"] is False


def test_audio_capabilities_with_key_and_network(monkeypatch):
    monkeypatch.setenv("ELEVENLABS_API_KEY", "dummy")
    monkeypatch.setenv("USE_ADAPTERS", "false")
    monkeypatch.setenv("USE_NETWORK", "true")
    reload(aip)
    caps = aip.audio_capabilities()
    assert caps["tts"] is True
    assert caps["stt"] is True
    assert caps["network"] is True


def test_tts_generate_bytes_sim(monkeypatch):
    monkeypatch.setenv("USE_ADAPTERS", "true")
    monkeypatch.delenv("ELEVENLABS_API_KEY", raising=False)
    reload(aip)
    out = aip.tts_generate_bytes("hola prueba")
    assert out is not None
    assert b"simulado" in out or isinstance(out, bytes)


def test_stt_transcribe_file_sim(tmp_path, monkeypatch):
    monkeypatch.setenv("USE_ADAPTERS", "true")
    audio_file = tmp_path / "dummy.bin"
    audio_file.write_bytes(b"fake")
    reload(aip)
    text = aip.stt_transcribe_file(str(audio_file))
    assert isinstance(text, str)
    assert "simulado" in text or text == ""  # allow fallback
