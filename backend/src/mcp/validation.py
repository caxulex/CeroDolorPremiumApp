from __future__ import annotations

# ruff: noqa: I001
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft7Validator


_ROOT = Path(__file__).resolve().parents[3]  # repo root
_CONTRACTS = _ROOT / "specs" / "001-description-esta-secci" / "contracts"


def _load_schema(name: str) -> dict[str, Any]:
    with (_CONTRACTS / name).open("r", encoding="utf-8") as f:
        return json.load(f)


_AIP_TO_ASD = Draft7Validator(_load_schema("aip_to_asd.json"))
_ASD_TO_AIPER = Draft7Validator(_load_schema("asd_to_aiper.json"))
_PATIENT_TO_CLINICIAN = Draft7Validator(_load_schema("patient_to_clinician.json"))
_CLINICIAN_TO_PHYSIO = Draft7Validator(_load_schema("clinician_to_physio.json"))
_PHYSIO_TO_PATIENT = Draft7Validator(_load_schema("physio_to_patient.json"))
_CLINICIAN_REPORT = Draft7Validator(_load_schema("clinician_report.json"))
_RESEARCH_QUERY = Draft7Validator(_load_schema("research_query.json"))
_DATA_OFFER = Draft7Validator(_load_schema("data_offer.json"))
_ANON_BUNDLE = Draft7Validator(_load_schema("anonymized_data_bundle.json"))
_MICRO_RCPT = Draft7Validator(_load_schema("micropayment_receipt.json"))
_AUDIT_LOG = Draft7Validator(_load_schema("audit_log_entry.json"))


def validate_aip_to_asd(payload: dict[str, Any]) -> list[str]:
    """Return a list of error messages (empty when valid)."""
    return [e.message for e in _AIP_TO_ASD.iter_errors(payload)]


def validate_asd_to_aiper(payload: dict[str, Any]) -> list[str]:
    """Return a list of error messages (empty when valid)."""
    return [e.message for e in _ASD_TO_AIPER.iter_errors(payload)]


def validate_patient_to_clinician(payload: dict[str, Any]) -> list[str]:
    """Return a list of error messages (empty when valid)."""
    return [e.message for e in _PATIENT_TO_CLINICIAN.iter_errors(payload)]


def validate_clinician_to_physio(payload: dict[str, Any]) -> list[str]:
    """Return a list of error messages (empty when valid)."""
    return [e.message for e in _CLINICIAN_TO_PHYSIO.iter_errors(payload)]


def validate_physio_to_patient(payload: dict[str, Any]) -> list[str]:
    """Return a list of error messages (empty when valid)."""
    return [e.message for e in _PHYSIO_TO_PATIENT.iter_errors(payload)]


def validate_clinician_report(payload: dict[str, Any]) -> list[str]:
    """Return a list of error messages (empty when valid)."""
    return [e.message for e in _CLINICIAN_REPORT.iter_errors(payload)]


def validate_research_query(payload: dict[str, Any]) -> list[str]:
    return [e.message for e in _RESEARCH_QUERY.iter_errors(payload)]


def validate_data_offer(payload: dict[str, Any]) -> list[str]:
    return [e.message for e in _DATA_OFFER.iter_errors(payload)]


def validate_anonymized_data_bundle(payload: dict[str, Any]) -> list[str]:
    return [e.message for e in _ANON_BUNDLE.iter_errors(payload)]


def validate_micropayment_receipt(payload: dict[str, Any]) -> list[str]:
    return [e.message for e in _MICRO_RCPT.iter_errors(payload)]


def validate_audit_log_entry(payload: dict[str, Any]) -> list[str]:
    return [e.message for e in _AUDIT_LOG.iter_errors(payload)]
