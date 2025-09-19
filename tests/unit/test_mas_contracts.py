from __future__ import annotations

from datetime import UTC, datetime

from backend.src.mcp.validation import (
    validate_clinician_to_physio,
    validate_patient_to_clinician,
    validate_physio_to_patient,
)


def _ts() -> str:
    return datetime.now(UTC).isoformat()


def test_patient_to_clinician_typical() -> None:
    payload = {
        "message_type": "patient_report",
        "patient_id": "p1",
        "timestamp": _ts(),
        "patient_report": {
            "pain_level": 6,
            "description": "dolor lumbar",
            "mood": "triste",
            "sleep_quality": "irregular",
        },
    }
    assert validate_patient_to_clinician(payload) == []


def test_patient_to_clinician_boundary_level() -> None:
    bad = {
        "message_type": "patient_report",
        "patient_id": "p1",
        "timestamp": _ts(),
        "patient_report": {"pain_level": 11, "description": "x"},
    }
    errs = validate_patient_to_clinician(bad)
    assert errs


def test_patient_to_clinician_invalid_mood_enum() -> None:
    bad = {
        "message_type": "patient_report",
        "patient_id": "p1",
        "timestamp": _ts(),
        "patient_report": {"pain_level": 5, "description": "x", "mood": "ecstatic"},
    }
    errs = validate_patient_to_clinician(bad)
    assert errs


def test_clinician_to_physio_typical() -> None:
    payload = {
        "message_type": "clinical_request",
        "patient_id": "p1",
        "timestamp": _ts(),
        "clinical_request": {
            "goal": "reduce_pain",
            "constraints": ["avoid_overexertion"],
            "insights": ["sleep_variability"],
        },
    }
    assert validate_clinician_to_physio(payload) == []


def test_clinician_to_physio_missing_goal() -> None:
    bad = {
        "message_type": "clinical_request",
        "patient_id": "p1",
        "timestamp": _ts(),
        "clinical_request": {
            # missing goal
            "constraints": ["avoid_overexertion"],
        },
    }
    errs = validate_clinician_to_physio(bad)
    assert errs


def test_clinician_to_physio_invalid_goal_enum() -> None:
    bad = {
        "message_type": "clinical_request",
        "patient_id": "p1",
        "timestamp": _ts(),
        "clinical_request": {
            "goal": "fix_everything",
        },
    }
    errs = validate_clinician_to_physio(bad)
    assert errs


def test_physio_to_patient_typical() -> None:
    payload = {
        "message_type": "exercise_plan",
        "patient_id": "p1",
        "timestamp": _ts(),
        "exercise_plan": {
            "items": [
                {"name": "stretch", "repetitions": 5, "frequency_per_day": 2, "notes": "gentle"}
            ]
        },
    }
    assert validate_physio_to_patient(payload) == []


def test_physio_to_patient_boundary_reps() -> None:
    bad = {
        "message_type": "exercise_plan",
        "patient_id": "p1",
        "timestamp": _ts(),
        "exercise_plan": {"items": [{"name": "walk", "repetitions": 0}]},
    }
    errs = validate_physio_to_patient(bad)
    assert errs


def test_physio_to_patient_invalid_item_name_enum() -> None:
    bad = {
        "message_type": "exercise_plan",
        "patient_id": "p1",
        "timestamp": _ts(),
        "exercise_plan": {"items": [{"name": "burpee", "repetitions": 5}]},
    }
    errs = validate_physio_to_patient(bad)
    assert errs


def test_physio_to_patient_missing_items() -> None:
    bad = {
        "message_type": "exercise_plan",
        "patient_id": "p1",
        "timestamp": _ts(),
        "exercise_plan": {},
    }
    errs = validate_physio_to_patient(bad)
    assert errs
