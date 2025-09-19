from __future__ import annotations

from pathlib import Path

from backend.src.services.research_network_service import (
    evaluate_query_against_patient,
    fulfill_query_offline,
)


def test_offline_flow_accepts_and_fulfills(tmp_path: Path) -> None:
    query = {
        "requester_id": "ai-1",
        "criteria": {"age_min": 30, "age_max": 40, "gender": "female", "diagnosis": "fibromialgia"},
        "requested_fields": ["activity", "sleep"],
        "compensation_sol": 0.05,
    }
    profile = {"age": 35, "gender": "female", "diagnosis": "fibromialgia"}
    patient_data = {"activity": [1000, 2000], "sleep": [6.5, 7.1], "pain_summaries": [3, 4]}

    assert evaluate_query_against_patient(query, profile) is True

    out = fulfill_query_offline(
        patient_id="p-1",
        patient_profile=profile,
        query=query,
        patient_data=patient_data,
        audit_log_path=tmp_path / "audit.jsonl",
    )
    assert "offer" in out and "bundle" in out and "receipt" in out
    assert Path(out["audit_log"]).exists() or (tmp_path / "audit.jsonl").exists()
