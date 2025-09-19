import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.src.agents.orchestrator import run_patient_cycle  # type: ignore
from backend.src.services import aip_service  # type: ignore
from backend.src.utils.persistence import store  # type: ignore

pid = "demo_patient_smoke"

# Run two cycles to accumulate events
c1 = run_patient_cycle({
    'patient_id': pid,
    'pain_level': 5,
    'pain_desc': 'molestia lumbar inicial',
    'mood': 'ok',
    'sleep': 'regular'
}, include_report=False)

c2 = run_patient_cycle({
    'patient_id': pid,
    'pain_level': 7,
    'pain_desc': 'aumento despues de actividad',
    'mood': 'cansado',
    'sleep': 'mal'
}, include_report=False)

sess = store.get(pid)
print('cycles_ok', bool(c1) and bool(c2))
print('event_count', len(sess.events))
print('last_event_type', sess.events[-1]['type'])
tts_bytes = aip_service.tts_generate_bytes('hola mundo') or b''
print('tts_prefix', tts_bytes[:30])
