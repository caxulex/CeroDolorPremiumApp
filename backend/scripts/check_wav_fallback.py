from backend.src.services import aip_service
b = aip_service.tts_generate_bytes('prueba de audio fallback WAV') or b''
print('len', len(b))
print('header', b[:12])
print('is_riff', b.startswith(b'RIFF'))
