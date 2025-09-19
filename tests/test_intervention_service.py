from backend.src.services.aiper_service import generate_intervention
from backend.src.utils.persistence import store


def _seed_events(pid: str, pain_levels, moods=None, sleeps=None):
    moods = moods or []
    sleeps = sleeps or []
    for lvl in pain_levels:
        store.append_event(pid, "pain_registration", {"pain": {"level": lvl}})
    for m in moods:
        store.append_event(pid, "mood_sleep", {"mood_sleep": {"mood": m, "sleep": "regular"}})
    for s in sleeps:
        store.append_event(pid, "mood_sleep", {"mood_sleep": {"mood": "neutral", "sleep": s}})


def test_intervention_high_pain_anomaly(tmp_path):
    pid = "test_patient_anomaly"
    _seed_events(pid, [3, 7, 10])  # jump triggers anomaly
    iv = generate_intervention(pid)
    assert isinstance(iv, dict)
    assert iv["intervention_type"] in {"breathing", "llm_suggestion"}


def test_intervention_mood_based(tmp_path):
    pid = "test_patient_mood"
    _seed_events(pid, [4, 5, 5], moods=["ansioso"])  # mood negative
    iv = generate_intervention(pid)
    assert iv["intervention_type"] in {"mindfulness", "llm_suggestion"}
