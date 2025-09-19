from __future__ import annotations

from backend.src.mcp.validation import validate_clinician_report
from backend.src.services.aic_service import generate_structured_report


def test_generate_structured_report_validates() -> None:
    report = generate_structured_report("patient-123", data={})
    errs = validate_clinician_report(report)
    assert errs == []


def test_generate_structured_report_has_min_fields() -> None:
    report = generate_structured_report("p2")
    # Schema validation is the main check; also assert key presence for clarity.
    for key in (
        "patient_id",
        "period",
        "highlights",
        "trends",
        "risk_flags",
        "patterns_detected",
        "adherence_summary",
        "recommendations",
    ):
        assert key in report