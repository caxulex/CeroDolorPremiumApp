import sys
sys.path.insert(0,'.')
from backend.src.services import aip_service  # type: ignore
b = aip_service.tts_generate_bytes('wav test offline deterministic') or b''
print('ok', b.startswith(b'RIFF'), len(b))
