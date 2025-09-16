import json
import subprocess
import sys
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from jsonschema import Draft7Validator

BACKEND = Path(__file__).resolve().parents[2]  # backend/src/mcp -> backend/
AGENTS = BACKEND / "src" / "agents"
AIP = AGENTS / "aip.py"
ASD = AGENTS / "asd.py"
AIPER = AGENTS / "aiper.py"
CONTRACTS = BACKEND.parent / "specs" / "001-description-esta-secci" / "contracts"


def envelope(source: str, target: str, payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": str(uuid.uuid4()),
        "ts": int(time.time() * 1000),
        "source": source,
        "target": target,
        "payload": payload,
    }


def _utc_iso() -> str:
    return datetime.now(UTC).isoformat()


def _load_schema(path: Path) -> Draft7Validator:
    schema = json.loads(path.read_text(encoding="utf-8"))
    return Draft7Validator(schema)


def _validate(obj: dict[str, Any], validator: Draft7Validator) -> tuple[bool, str | None]:
    errors = sorted(validator.iter_errors(obj), key=lambda e: e.path)
    if errors:
        return False, errors[0].message
    return True, None


def run_agent(path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    proc = subprocess.run(  # noqa: S603
        [sys.executable, str(path)],
        input=json.dumps(payload).encode(),
        capture_output=True,
        check=True,
    )
    out = proc.stdout.decode() or "{}"
    return json.loads(out)


def main() -> None:
    # Start with a minimal input; we'll build contract-compliant messages
    start = {"patient_id": "demo_patient", "pain_level": 5, "pain_desc": "placeholder"}
    transcript = []

    # Build AIP->ASD message per contract and validate
    pain_msg = {
        "message_type": "pain_submission",
        "patient_id": start.get("patient_id", "demo_patient"),
        "timestamp": _utc_iso(),
        "pain_data": {
            "level": int(start.get("pain_level", 5)),
            "description": start.get("pain_desc", "placeholder"),
            "mood": start.get("mood", "neutral"),
            "sleep_quality": start.get("sleep", "desconocido"),
        },
    }
    v1 = _load_schema(CONTRACTS / "aip_to_asd.json")
    v1_ok, v1_err = _validate(pain_msg, v1)

    e1 = envelope("router", "AIP", pain_msg)
    transcript.append({"send": e1, "validation": {"aip_to_asd": {"ok": v1_ok, "error": v1_err}}})
    r1 = run_agent(AIP, e1["payload"])  # agents only see payload for now
    transcript.append({"recv": {"from": "AIP", "payload": r1}})

    # Build ASD->AIPer message per contract and validate
    insights_obj = r1.get("insights") if isinstance(r1, dict) else None
    patterns = []
    if isinstance(insights_obj, dict):
        pd = insights_obj.get("patterns_detected")
        if isinstance(pd, list) and all(isinstance(x, str) for x in pd):
            patterns = pd
    if not patterns:
        patterns = ["placeholder"]

    insights_msg = {
        "message_type": "insights",
        "patient_id": pain_msg["patient_id"],
        "timestamp": _utc_iso(),
        "insights": {"patterns_detected": patterns},
    }
    v2 = _load_schema(CONTRACTS / "asd_to_aiper.json")
    v2_ok, v2_err = _validate(insights_msg, v2)

    e2 = envelope("AIP", "ASD", insights_msg)
    transcript.append({"send": e2, "validation": {"asd_to_aiper": {"ok": v2_ok, "error": v2_err}}})
    r2 = run_agent(ASD, e2["payload"])  # still payload-only
    transcript.append({"recv": {"from": "ASD", "payload": r2}})

    e3 = envelope("ASD", "AIPer", insights_msg)
    transcript.append({"send": e3})
    r3 = run_agent(AIPER, e3["payload"])  # payload-only
    transcript.append({"recv": {"from": "AIPer", "payload": r3}})

    result = {"transcript": transcript, "final": r3}
    print(json.dumps(result, indent=2))  # noqa: T201


if __name__ == "__main__":
    main()
