"""Lightweight JSON file backed session persistence.

Each patient/session is stored in a simple structure:
{
  "patient_id": str,
  "events": [
      {"id": int, "ts": iso8601 str, "type": str, "data": {...}}
  ],
  "meta": {"created_ts": iso str, "updated_ts": iso str}
}

Design goals:
 - No external deps
 - Safe concurrent-ish append (best effort, overwrite last write wins)
 - Resistant to partial write via temp file + atomic replace on same filesystem
 - Small API surface for UI usage
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List
import json
import threading
from datetime import datetime, timezone


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Session:
    patient_id: str
    events: List[Dict[str, Any]] = field(default_factory=list)
    meta: Dict[str, Any] = field(default_factory=lambda: {"created_ts": _utc_now_iso(), "updated_ts": _utc_now_iso()})

    def to_dict(self) -> Dict[str, Any]:  # pragma: no cover - trivial
        return {
            "patient_id": self.patient_id,
            "events": self.events,
            "meta": self.meta,
        }


class SessionStore:
    def __init__(self, root: Path):
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._cache: Dict[str, Session] = {}

    # ---------------- Public API ---------------- #
    def get(self, patient_id: str) -> Session:
        with self._lock:
            if patient_id in self._cache:
                return self._cache[patient_id]
            session = self._load_from_disk(patient_id)
            self._cache[patient_id] = session
            return session

    def append_event(self, patient_id: str, event_type: str, data: Dict[str, Any]):
        with self._lock:
            session = self.get(patient_id)
            next_id = (session.events[-1]["id"] + 1) if session.events else 1
            event = {
                "id": next_id,
                "ts": _utc_now_iso(),
                "type": event_type,
                "data": data,
            }
            session.events.append(event)
            session.meta["updated_ts"] = _utc_now_iso()
            self._save_to_disk(session)
            return event

    def export_json(self, patient_id: str) -> str:
        session = self.get(patient_id)
        return json.dumps(session.to_dict(), ensure_ascii=False, indent=2)

    def list_sessions(self) -> List[str]:  # pragma: no cover - not used yet
        return [p.stem for p in self.root.glob("*.json")]

    # ---------------- Internal helpers ---------------- #
    def _session_path(self, patient_id: str) -> Path:
        safe = "".join(c for c in patient_id if c.isalnum() or c in ("-", "_")) or "session"
        return self.root / f"{safe}.json"

    def _load_from_disk(self, patient_id: str) -> Session:
        path = self._session_path(patient_id)
        if not path.exists():
            return Session(patient_id=patient_id)
        try:
            content = json.loads(path.read_text(encoding="utf-8"))
            sess = Session(
                patient_id=content.get("patient_id", patient_id),
                events=content.get("events", []),
                meta=content.get("meta", {}),
            )
            # Backfill meta fields if missing
            if "created_ts" not in sess.meta:
                sess.meta["created_ts"] = _utc_now_iso()
            if "updated_ts" not in sess.meta:
                sess.meta["updated_ts"] = _utc_now_iso()
            return sess
        except Exception:  # pragma: no cover - defensive
            # Corrupt file fallback
            return Session(patient_id=patient_id)

    def _save_to_disk(self, session: Session):
        path = self._session_path(session.patient_id)
        tmp = path.with_suffix(".json.tmp")
        data = session.to_dict()
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(path)


# Global shared store instance (backend/sessions)
store = SessionStore(Path(__file__).resolve().parents[2] / "sessions")

__all__ = ["Session", "SessionStore", "store"]
