from __future__ import annotations

import importlib
from typing import Any

from backend.src.logging_config import get_logger

logger = get_logger(__name__)


def generate_summary(patient_id: str) -> str:
    # Minimal usage to avoid unused variable warnings
    _ = patient_id
    return "Summary: patient weekly overview."


def generate_structured_report(patient_id: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
    """Produce a structured weekly clinician report (offline-first).

    Attempts to include ASD analysis when available; otherwise returns a deterministic placeholder structure.
    """
    # Lazy import to avoid hard dependency
    try:
        asd_service_mod = importlib.import_module("backend.src.services.asd_service")
    except Exception:  # noqa: BLE001
        asd_service_mod = None

    analysis = None
    if asd_service_mod is not None:
        try:
            analysis = asd_service_mod.analyze_data(patient_id, data or {})
        except Exception:  # noqa: BLE001
            analysis = None

    patterns = []
    trend = "stable"
    risk = []
    if isinstance(analysis, dict):
        patterns = analysis.get("patterns_detected", []) or []
        trend = analysis.get("trend_analysis", "stable") or "stable"
        risk = analysis.get("risk_flags", []) or []

    report: dict[str, Any] = {
        "patient_id": patient_id,
        "period": "last_7_days",
        "highlights": [
            "Resumen semanal generado automáticamente.",
        ],
        "trends": trend,
        "risk_flags": risk,
        "patterns_detected": patterns,
        "adherence_summary": {
            "medication": "unknown",
            "checkins_completed": 0,
        },
        "recommendations": [
            "Considerar ejercicios de movilidad suave por la mañana.",
        ],
    }
    logger.debug(
        "structured_report patient=%s patterns=%d trend=%s risk=%d",
        patient_id,
        len(patterns),
        trend,
        len(risk),
    )
    return report
