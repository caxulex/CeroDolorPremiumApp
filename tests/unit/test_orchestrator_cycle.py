from __future__ import annotations

from backend.src.agents.orchestrator import run_patient_cycle
from backend.src.utils.persistence import store


def test_run_patient_cycle_creates_events():
    pid = "orch_test_patient"
    before_len = len(store.get(pid).events)
    cycle = run_patient_cycle({
        "patient_id": pid,
        "pain_level": 7,
        "pain_desc": "lumbar agudo",
        "mood": "ansioso",
        "sleep": "malo",
    })
    assert cycle["patient_id"] == pid
    assert "aip" in cycle and cycle["aip"].get("pain", {}).get("level") == 7
    assert "asd" in cycle and isinstance(cycle["asd"].get("patterns_detected", []), list)
    assert "aiper" in cycle and cycle["aiper"].get("suggestion")
    assert "aic" in cycle and cycle["aic"].get("report", {})
    after_events = store.get(pid).events
    assert len(after_events) > before_len
    # Ensure orchestrated_cycle event appended
    assert any(e.get("type") == "orchestrated_cycle" for e in after_events)
