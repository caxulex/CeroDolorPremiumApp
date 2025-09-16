from __future__ import annotations

from backend.src.mcp.validation import (
    validate_research_query,
    validate_data_offer,
    validate_anonymized_data_bundle,
    validate_micropayment_receipt,
    validate_audit_log_entry,
)


def test_research_query_schema_valid() -> None:
    q = {
        "requester_id": "ai-1",
        "criteria": {"age_min": 30, "age_max": 40, "gender": "female", "diagnosis": "fibromialgia"},
        "requested_fields": ["activity", "sleep"],
        "compensation_sol": 0.05,
    }
    assert validate_research_query(q) == []


def test_data_offer_schema_valid() -> None:
    offer = {
        "patient_id": "p-1",
        "wallet_address": "addr123456789",
        "fields": ["activity"],
        "anonymized_hash": "abcdef0123456789",
    }
    assert validate_data_offer(offer) == []


def test_anonymized_bundle_schema_valid() -> None:
    bundle = {"bundle_id": "bundle-xyz", "fields": ["sleep"], "data": {"sleep": [1, 2, 3]}}
    assert validate_anonymized_data_bundle(bundle) == []


def test_micropayment_receipt_valid() -> None:
    rcpt = {"to": "addr123456789", "amount_sol": 0.01, "signature": "deadbeefcafebabe"}
    assert validate_micropayment_receipt(rcpt) == []


def test_audit_log_entry_valid() -> None:
    from datetime import UTC, datetime

    entry = {
        "ts": datetime.now(UTC).isoformat(),
        "actor": "AP",
        "action": "request",
        "resource": "research_query",
        "details": {"foo": "bar"},
    }
    assert validate_audit_log_entry(entry) == []
