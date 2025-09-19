from __future__ import annotations

from backend.src.agents.network_orchestrator import broadcast_research_query
from backend.src.services import consent_service
from backend.src.services.anonymization_service import anonymize_payload

PROFILE = {"age": 35, "gender": "female", "diagnosis": "fibromyalgia"}
PATIENT_DATA = {"pain_logs": [4,5,6], "mood_sleep": {"mood": "neutral"}, "activity": 1500}


def test_consent_grant_and_revoke_cycle():
    pid = "p_consent"
    rec = consent_service.grant_consent(pid, "pain_logs", "clinico_1")
    assert rec.granted is True
    assert consent_service.has_consent(pid, "pain_logs", "clinico_1")
    ok = consent_service.revoke_consent(pid, "pain_logs", "clinico_1")
    assert ok is True
    assert consent_service.has_consent(pid, "pain_logs", "clinico_1") is False


def test_research_flow_requires_consent():
    pid = "p_research"
    query = {
        "requester_id": "research_org_1",
        "criteria": {"age_min": 30, "age_max": 40, "gender": "female"},
        "requested_fields": ["pain_logs", "mood_sleep"],
        "compensation_sol": 0.001,
    }
    # No consent yet -> expect missing consent error
    res = broadcast_research_query(
        patient_id=pid,
        patient_profile=PROFILE,
        query=query,
        patient_data=PATIENT_DATA,
    )
    assert res.get("fulfilled") is False
    assert "error" in res and "missing_consent_for" in str(res["error"])  # type: ignore[index]
    # Grant partial (only pain_logs) still should fail for mood_sleep
    consent_service.grant_consent(pid, "pain_logs", "research_org_1")
    res2 = broadcast_research_query(
        patient_id=pid,
        patient_profile=PROFILE,
        query=query,
        patient_data=PATIENT_DATA,
    )
    assert res2.get("fulfilled") is False and "mood_sleep" in str(res2.get("error"))
    # Grant remaining
    consent_service.grant_consent(pid, "mood_sleep", "research_org_1")
    res3 = broadcast_research_query(
        patient_id=pid,
        patient_profile=PROFILE,
        query=query,
        patient_data=PATIENT_DATA,
    )
    assert res3.get("fulfilled") is True
    assert res3.get("result")


def test_anonymization_hash_stability():
    d = {"a":1, "b":2}
    anon1 = anonymize_payload(d, ["a","b"])
    anon2 = anonymize_payload({"b":2, "a":1}, ["a","b"])
    assert anon1["hash"] == anon2["hash"]
