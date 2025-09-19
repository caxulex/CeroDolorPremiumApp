"""Network orchestrator for Project B (AP, AC, AI) offline-first flows.

Provides high-level functions:
 - submit_clinician_request(patient_id, requester, data_types)
 - grant_clinician_request(patient_id, requester, data_types)
 - broadcast_research_query(patient_id, profile, query, patient_data)

Clinician request is a two-step flow (request then explicit grant of consent per data_type).
Research query uses existing fulfill_query_offline after verifying consents.
"""
from __future__ import annotations

from typing import Any, Dict, List

from backend.src.services import consent_service
from backend.src.services.research_network_service import (
    evaluate_query_against_patient,
    fulfill_query_offline,
)
from backend.src.utils.persistence import store


def submit_clinician_request(patient_id: str, requester: str, data_types: List[str]) -> dict[str, Any]:
    payload = {"requester": requester, "data_types": data_types}
    store.append_event(patient_id, "clinician_request", {"request": payload})
    return {"accepted": True, "pending": data_types}


def grant_clinician_request(patient_id: str, requester: str, data_types: List[str]) -> dict[str, Any]:
    granted: List[str] = []
    for dt in data_types:
        consent_service.grant_consent(patient_id, dt, requester)
        granted.append(dt)
    return {"granted": granted}


def revoke_clinician_access(patient_id: str, requester: str, data_types: List[str]) -> dict[str, Any]:
    revoked: List[str] = []
    for dt in data_types:
        if consent_service.revoke_consent(patient_id, dt, requester):
            revoked.append(dt)
    return {"revoked": revoked}


def broadcast_research_query(
    *,
    patient_id: str,
    patient_profile: dict[str, Any],
    query: dict[str, Any],
    patient_data: dict[str, Any],
) -> dict[str, Any]:
    if not evaluate_query_against_patient(query, patient_profile):
        store.append_event(patient_id, "research_query_ignored", {"query": query})
        return {"matched": False, "reason": "criteria_not_met"}
    store.append_event(patient_id, "research_query_received", {"query": query})
    # Fulfillment path will enforce consent; if missing, caller should grant first.
    res = fulfill_query_offline(
        patient_id=patient_id,
        patient_profile=patient_profile,
        query=query,
        patient_data=patient_data,
    )
    if "error" in res:
        store.append_event(patient_id, "research_fulfill_error", {"error": res["error"]})
        return {"matched": True, "fulfilled": False, "error": res["error"]}
    store.append_event(patient_id, "research_fulfilled", {"result": res})
    return {"matched": True, "fulfilled": True, "result": res}


__all__ = [
    "submit_clinician_request",
    "grant_clinician_request",
    "revoke_clinician_access",
    "broadcast_research_query",
]
