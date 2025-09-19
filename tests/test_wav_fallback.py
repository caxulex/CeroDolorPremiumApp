from backend.src.services.aip_service import tts_generate_bytes


def test_wav_fallback_header():
    wav = tts_generate_bytes("hola mundo", voice="demo_female")
    assert isinstance(wav, (bytes, bytearray))
    assert wav[:4] == b"RIFF"
    assert b"WAVE" in wav[0:16]
