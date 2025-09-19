"""Consent & permission management (offline-first).

Stores consent grants per patient in-memory + SessionStore events.
Structure:
  _CONSENTS = { patient_id: { key(tuple): { 'granted': bool, 'ts': iso, 'revoked_ts': iso|None }}}

Key tuple fields:
  (data_type, requester, scope)
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Dict, Tuple, Optional, Any

from backend.src.utils.persistence import store


def _now() -> str:
    return datetime.now(UTC).isoformat()


ConsentKey = Tuple[str, str, str]  # data_type, requester, scope


@dataclass
class ConsentRecord:
    data_type: str
    requester: str
    scope: str
    granted: bool
    ts: str
    revoked_ts: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:  # pragma: no cover - trivial
        return {
            "data_type": self.data_type,
            "requester": self.requester,
            "scope": self.scope,
            "granted": self.granted,
            "ts": self.ts,
            "revoked_ts": self.revoked_ts,
        }


_CONSENTS: Dict[str, Dict[ConsentKey, ConsentRecord]] = {}


def grant_consent(patient_id: str, data_type: str, requester: str, scope: str = "read") -> ConsentRecord:
    bucket = _CONSENTS.setdefault(patient_id, {})
    key: ConsentKey = (data_type, requester, scope)
    rec = ConsentRecord(data_type=data_type, requester=requester, scope=scope, granted=True, ts=_now())
    bucket[key] = rec
    store.append_event(patient_id, "consent_grant", {"consent": rec.to_dict()})
    return rec


def revoke_consent(patient_id: str, data_type: str, requester: str, scope: str = "read") -> bool:
    bucket = _CONSENTS.get(patient_id, {})
    key: ConsentKey = (data_type, requester, scope)
    rec = bucket.get(key)
    if not rec:
        return False
    if rec.revoked_ts is None:
        rec.revoked_ts = _now()
        rec.granted = False
        store.append_event(patient_id, "consent_revoke", {"consent": rec.to_dict()})
    return True


def has_consent(patient_id: str, data_type: str, requester: str, scope: str = "read") -> bool:
    rec = _CONSENTS.get(patient_id, {}).get((data_type, requester, scope))
    return bool(rec and rec.granted and rec.revoked_ts is None)


def list_consents(patient_id: str) -> list[dict[str, Any]]:
    bucket = _CONSENTS.get(patient_id, {})
    return [r.to_dict() for r in bucket.values()]


__all__ = [
    "grant_consent",
    "revoke_consent",
    "has_consent",
    "list_consents",
]
