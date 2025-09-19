"""Lightweight in-memory + last-persist snapshot caching.

Avoids recomputing full analytics snapshot repeatedly within a single
Streamlit session for the same patient events list.
"""
from __future__ import annotations
from typing import Any, Dict, List, Tuple
import threading
import hashlib
import json

from .analytics import build_analytics_snapshot  # type: ignore

_LOCK = threading.RLock()
# Cache structure: { patient_id: (events_hash, snapshot_dict) }
_CACHE: Dict[str, Tuple[str, Dict[str, Any]]] = {}


def _hash_events(events: List[Dict[str, Any]]) -> str:
    # Stable hash over event ids + types + pain levels (subset) to avoid huge payload hashing cost
    mini = []
    for ev in events:
        try:
            et = ev.get("type")
            eid = ev.get("id")
            pain_val = None
            if ev.get("type") == "pain_registration":
                p = ev.get("data", {}).get("pain", {})
                if isinstance(p, dict):
                    pain_val = p.get("pain_level") or p.get("level") or p.get("value")
            mini.append((eid, et, pain_val))
        except Exception:  # noqa: BLE001
            continue
    raw = json.dumps(mini, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()


def compute_or_get_snapshot(events: List[Dict[str, Any]], patient_id: str) -> Dict[str, Any]:
    """Return cached analytics snapshot if events unchanged, else recompute.

    Parameters
    ----------
    events: list of session events (ordered)
    patient_id: str unique patient identifier
    """
    if not events:
        return {}
    ev_hash = _hash_events(events)
    with _LOCK:
        cached = _CACHE.get(patient_id)
        if cached and cached[0] == ev_hash:
            return {"_cache_hit": True, **cached[1]}
        # Recompute
        snap = build_analytics_snapshot(events)
        _CACHE[patient_id] = (ev_hash, snap)
        return {"_cache_hit": False, **snap}


def clear_snapshot_cache(patient_id: str | None = None) -> None:
    with _LOCK:
        if patient_id is None:
            _CACHE.clear()
        else:
            _CACHE.pop(patient_id, None)
