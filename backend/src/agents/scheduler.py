"""Lightweight scheduling helpers for clinician report generation.

This avoids external cron dependencies. The UI / orchestrator can call
`maybe_generate_weekly_report(patient_id)` opportunistically (e.g. on login or
after a new check-in). If 7 days have elapsed since the last clinician_report
event, a new report is generated and persisted.
"""
from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from backend.src.utils.persistence import store
from backend.src.services import aic_service


def _parse_iso(ts: str) -> datetime | None:  # pragma: no cover - small helper
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except Exception:
        return None


def _last_report_event(patient_id: str) -> dict[str, Any] | None:
    sess = store.get(patient_id)
    for ev in reversed(sess.events):  # iterate from newest
        if ev.get("type") == "clinician_report":
            return ev
    return None


def needs_weekly_report(patient_id: str, *, interval_days: int = 7) -> bool:
    ev = _last_report_event(patient_id)
    if not ev:
        return True
    ts = ev.get("ts")
    if not isinstance(ts, str):
        return True
    dt = _parse_iso(ts)
    if not dt:
        return True
    return datetime.now(UTC) - dt >= timedelta(days=interval_days)


def maybe_generate_weekly_report(patient_id: str) -> dict[str, Any] | None:
    if not needs_weekly_report(patient_id):
        return None
    report = aic_service.generate_structured_report(patient_id)
    store.append_event(patient_id, "clinician_report", {"report": report, "auto": True})
    return report


__all__ = [
    "needs_weekly_report",
    "maybe_generate_weekly_report",
]
