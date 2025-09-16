from __future__ import annotations

from datetime import datetime, timezone
import pytest

from backend.src.models import Patient, PainRecord, Clinician, Agent, AgentType


def test_pain_record_valid_range() -> None:
    rec = PainRecord(datetime.now(timezone.utc), 5, description="ok")
    assert rec.pain_level == 5


@pytest.mark.parametrize("level", [0, 11])
def test_pain_record_invalid_range(level: int) -> None:
    with pytest.raises(ValueError):
        PainRecord(datetime.now(timezone.utc), level)


def test_patient_add_pain_record() -> None:
    p = Patient("p1", "Alice")
    rec = PainRecord(datetime.now(timezone.utc), 3)
    p.add_pain_record(rec)
    assert p.pain_history[-1] is rec


def test_clinician_add_patient() -> None:
    c = Clinician("c1", "Dr. Who")
    c.add_patient("p1")
    c.add_patient("p1")  # idempotent
    assert c.patients == ["p1"]


def test_agent_state_roundtrip() -> None:
    a = Agent(AgentType.AIP)
    a.set("mood", "calm")
    assert a.get("mood") == "calm"
    assert a.get("missing", "fallback") == "fallback"
