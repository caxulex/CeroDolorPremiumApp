import json
from pathlib import Path

from backend.src.utils.persistence import SessionStore


def test_session_append_and_export(tmp_path: Path):
    store = SessionStore(tmp_path)
    store.append_event("patientX", "start", {"foo": 1})
    store.append_event("patientX", "second", {"bar": 2})

    exported = store.export_json("patientX")
    data = json.loads(exported)
    assert data["patient_id"] == "patientX"
    assert len(data["events"]) == 2
    assert data["events"][0]["id"] == 1
    assert data["events"][1]["id"] == 2
    # Ensure meta timestamps exist
    assert "created_ts" in data["meta"]
    assert "updated_ts" in data["meta"]

    # Reload store and ensure persistence
    store2 = SessionStore(tmp_path)
    sess = store2.get("patientX")
    assert len(sess.events) == 2
