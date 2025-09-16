from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from backend.src.mcp.validation import validate_clinician_report


def _read_json(text: str) -> dict:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {}


def test_router_mas_demo_with_aic() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    router_py = repo_root / "backend" / "src" / "agents" / "router.py"
    python_bin = Path(sys.executable)

    payload = {
        "patient_id": "it-patient",
        "pain_level": 5,
        "pain_desc": "dolor",
        "mood": "neutral",
        "sleep": "ok",
    }

    proc = subprocess.run(  # noqa: S603
        [str(python_bin), str(router_py), "--mas-demo", "--include-aic", "--payload", json.dumps(payload)],
        capture_output=True,
        text=True,
        check=True,
    )

    out = _read_json(proc.stdout)
    assert isinstance(out, dict)
    assert "aic_report" in out

    errs = validate_clinician_report(out["aic_report"])  # type: ignore[typeddict-item]
    assert errs == []
