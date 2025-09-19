from typing import Any


def anonymize_sessions(sessions: list[dict[str, Any]], _level: str = "safe-default") -> list[dict[str, Any]]:
    result = []
    for s in sessions:
        evs = []
        for ev in s.get("events", []):
            data = dict(ev.get("data") or {})
            data.pop("patient_name", None)
            evs.append({"type": ev.get("type"), "data": data})
        result.append({"patient_id": "anon", "events": evs})
    return result
