from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from backend.src.mcp.validation import (
    validate_anonymized_data_bundle,
    validate_audit_log_entry,
    validate_data_offer,
    validate_micropayment_receipt,
    validate_research_query,
)
from backend.src.services.data_wallet_service import (
    create_patient_wallet,
    grant_consent_and_pay,
    mint_data_asset,
)


def _ts() -> str:
    return datetime.now(UTC).isoformat()


def _hash_data(obj: Any) -> str:
    # Deterministic anonymization surrogate
    data = json.dumps(obj, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def _log_entry(actor: str, action: str, resource: str, details: dict[str, Any]) -> dict[str, Any]:
    return {"ts": _ts(), "actor": actor, "action": action, "resource": resource, "details": details}


def _append_audit(entry: dict[str, Any], path: Path) -> None:
    # Validate entry shape and append to a JSONL file in repo root (under backend/) for demo
    errs = validate_audit_log_entry(entry)
    if errs:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def evaluate_query_against_patient(query: dict[str, Any], patient_profile: dict[str, Any]) -> bool:
    """Offline filter to decide if a patient's AP responds to AI's query.

    Minimal criteria supported: age range, gender, diagnosis match (if present in patient_profile).
    """
    # Always validate query shape first
    if validate_research_query(query):
        return False
    crit = query.get("criteria", {}) if isinstance(query, dict) else {}
    age = patient_profile.get("age")
    if isinstance(age, int):
        if "age_min" in crit and isinstance(crit.get("age_min"), int) and age < crit["age_min"]:
            return False
        if "age_max" in crit and isinstance(crit.get("age_max"), int) and age > crit["age_max"]:
            return False
    gender = patient_profile.get("gender")
    if crit.get("gender") and gender and crit["gender"] != gender:
        return False
    diagnosis = patient_profile.get("diagnosis")
    return not (crit.get("diagnosis") and diagnosis and crit["diagnosis"] not in str(diagnosis))


def fulfill_query_offline(
    *,
    patient_id: str,
    patient_profile: dict[str, Any],  # reserved for future consent policy hooks
    query: dict[str, Any],
    patient_data: dict[str, Any],
    audit_log_path: Path | None = None,
) -> dict[str, Any]:
    """Simulate AP side fulfillment: mint data asset, grant consent, micropayment, and return bundle.

    Returns a dict with keys: offer, bundle, receipt, audit_log (optional path).
    """
    # Touch unused arg to satisfy linters until consent policy hooks are implemented
    _ = patient_profile
    # Validate query first
    q_errs = validate_research_query(query)
    if q_errs:
        return {"error": {"query": q_errs}}

    # Create/derive wallet and mint a data token for the anonymized payload
    wallet = create_patient_wallet(patient_id)
    address = wallet.get("address") if isinstance(wallet, dict) else None
    if not address:
        # Offline fallback pseudo-address
        address = f"addr-{_hash_data({'patient_id': patient_id})[:12]}"
    anon_hash = _hash_data({k: patient_data.get(k) for k in query.get("requested_fields", [])})

    offer = {
        "patient_id": patient_id,
        "wallet_address": address or "",
        "fields": query.get("requested_fields", []),
        "anonymized_hash": anon_hash,
    }
    offer_errs = validate_data_offer(offer)
    if offer_errs:
        return {"error": {"offer": offer_errs}}

    mint_resp = mint_data_asset(address or "", anonymized_hash=anon_hash)
    token_id = mint_resp.get("token_id") if isinstance(mint_resp, dict) else None
    if not token_id:
        token_id = f"tok-{anon_hash[:12]}"

    # Package anonymized bundle
    bundle = {
        "bundle_id": f"bundle-{patient_id}",
        "fields": query.get("requested_fields", []),
        "data": {k: patient_data.get(k) for k in query.get("requested_fields", [])},
    }
    b_errs = validate_anonymized_data_bundle(bundle)
    if b_errs:
        return {"error": {"bundle": b_errs}}

    # Consent + micropayment (offline signature)
    comp = float(query.get("compensation_sol", 0))
    grant = grant_consent_and_pay(token_id or "", str(address or ""), comp)
    receipt = {
        "to": str(address or ""),
        "amount_sol": comp,
        "signature": (grant.get("payment_signature") if isinstance(grant, dict) else None) or f"sig-{_hash_data({'p': patient_id, 'c': comp})[:16]}",
    }
    r_errs = validate_micropayment_receipt(receipt)
    if r_errs:
        return {"error": {"receipt": r_errs}}

    # Write audit entries
    if audit_log_path is None:
        audit_log_path = Path(__file__).resolve().parents[2] / "audit" / "project_b.jsonl"
    _append_audit(_log_entry("AI", "request", "research_query", {"requester": query.get("requester_id")}), audit_log_path)
    _append_audit(_log_entry("AP", "approve", "data_access", {"patient_id": patient_id}), audit_log_path)
    _append_audit(_log_entry("AP", "fulfill", "data_bundle", {"bundle_id": bundle["bundle_id"]}), audit_log_path)
    _append_audit(_log_entry("AP", "transfer", "nft", {"token_id": token_id}), audit_log_path)
    _append_audit(_log_entry("AI", "pay", "solana_micropayment", {"amount": comp}), audit_log_path)

    return {
        "offer": offer,
        "bundle": bundle,
        "receipt": receipt,
        "audit_log": str(audit_log_path),
    }
