"""Unified multi-agent orchestration layer.

This module provides an in-process API to run the conceptual flow:

  AIP (collect input) -> ASD (analyze) -> AIPer (intervention) -> AIC (clinician report)

Design goals:
 - Offline-first & deterministic (no network unless env flags set)
 - Reuse existing service facades (aip_service, asd_service, aiper_service, aic_service)
 - Provide a simple Orchestrator class with a single public `run_cycle` method
 - Small data contracts using TypedDict for clarity without introducing pydantic overhead

The UI can import `run_patient_cycle` for a single high-level call.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Dict, List, Optional, TypedDict

from backend.src.services import (
    aip_service,
    asd_service,
    aiper_service,
    aic_service,
)
from backend.src.utils.persistence import store
from backend.src.agents.scheduler import maybe_generate_weekly_report


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


class PatientInput(TypedDict, total=False):
    patient_id: str
    pain_level: int
    pain_desc: str
    mood: str
    sleep: str


class AIPOutput(TypedDict, total=False):
    message: str
    pain: Dict[str, Any]
    mood_sleep: Dict[str, Any]


class ASDOutput(TypedDict, total=False):
    patterns_detected: List[str]
    trend_analysis: str
    risk_flags: List[str]


class AIPerOutput(TypedDict, total=False):
    suggestion: str
    intervention_type: str
    details: Dict[str, Any]


class AICOutput(TypedDict, total=False):
    report: Dict[str, Any]


class OrchestratedCycle(TypedDict, total=False):
    patient_id: str
    ts: str
    aip: AIPOutput
    asd: ASDOutput
    aiper: AIPerOutput
    aic: AICOutput


@dataclass(slots=True)
class Orchestrator:
    include_report: bool = True

    def run_cycle(self, patient: PatientInput) -> OrchestratedCycle:
        """Run the full pipeline for a patient's current subjective input.

        Steps:
          1. AIP registers pain + mood/sleep & feedback
          2. ASD analyzes combined data
          3. AIPer generates proactive intervention
          4. (Optional) AIC produces structured clinician report
          5. Persist each hop as an event in SessionStore
        """
        pid = patient.get("patient_id") or "demo_patient"
        pain_level = int(patient.get("pain_level", 5))
        pain_desc = patient.get("pain_desc") or "(sin descripcion)"
        mood = patient.get("mood") or "neutral"
        sleep = patient.get("sleep") or "regular"

        # AIP
        pain = aip_service.register_pain(pid, pain_level, pain_desc)
        mood_sleep = aip_service.register_mood_sleep(pid, mood, sleep)
        store.append_event(pid, "pain_registration", {"pain": pain})
        store.append_event(pid, "mood_sleep", {"mood_sleep": mood_sleep})
        aip_out: AIPOutput = {
            "message": "captured",
            "pain": pain,
            "mood_sleep": mood_sleep,
        }

        # ASD
        asd_in = {"pain": pain, "mood_sleep": mood_sleep}
        asd_res = asd_service.analyze_data(pid, asd_in)
        store.append_event(pid, "insights", {"insights": asd_res})
        asd_out: ASDOutput = {
            "patterns_detected": list(asd_res.get("patterns_detected", [])),
            "trend_analysis": asd_res.get("trend_analysis", "stable"),
            "risk_flags": list(asd_res.get("risk_flags", [])),
        }

        # AIPer
        intervention = aiper_service.generate_intervention(pid)
        # Backwards compatibility if service returns just string
        if isinstance(intervention, str):
            store.append_event(pid, "suggestion", {"suggestion": intervention})
            aiper_out = {"suggestion": intervention}
        else:
            store.append_event(
                pid,
                "intervention",
                {
                    "suggestion": intervention.get("suggestion"),
                    "intervention_type": intervention.get("intervention_type"),
                    "details": intervention.get("details", {}),
                },
            )
            aiper_out = {
                "suggestion": intervention.get("suggestion", ""),
                "intervention_type": intervention.get("intervention_type", "unknown"),
                "details": intervention.get("details", {}),
            }

        # AIC
        aic_out: AICOutput = {"report": {}}
        if self.include_report:
            report = aic_service.generate_structured_report(pid, {"aip": aip_out, "asd": asd_out})
            store.append_event(pid, "clinician_report", {"report": report})
            aic_out = {"report": report}

        # Opportunistic weekly auto-report (will no-op if not due)
        if self.include_report:
            auto = maybe_generate_weekly_report(pid)
            if auto:
                # If an auto report just generated, reflect it (keeping manual one as primary)
                aic_out = {"report": auto}

        cycle: OrchestratedCycle = {
            "patient_id": pid,
            "ts": _utc_now(),
            "aip": aip_out,
            "asd": asd_out,
            "aiper": aiper_out,
            "aic": aic_out,
        }
        store.append_event(pid, "orchestrated_cycle", {"cycle": cycle})
        return cycle


_DEFAULT_ORCH = Orchestrator()


def run_patient_cycle(patient: PatientInput, *, include_report: bool = True) -> OrchestratedCycle:
    orch = _DEFAULT_ORCH if include_report else Orchestrator(include_report=False)
    return orch.run_cycle(patient)


__all__ = [
    "PatientInput",
    "OrchestratedCycle",
    "run_patient_cycle",
    "Orchestrator",
]
