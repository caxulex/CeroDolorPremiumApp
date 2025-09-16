from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def test_router_mas_demo_flow() -> None:
    root = Path(__file__).resolve().parents[2]
    python = Path(sys.executable)
    router = root / "backend" / "src" / "agents" / "router.py"

    payload = {
        "patient_id": "p_demo",
        "pain_level": 5,
        "pain_desc": "dolor lumbar al despertar",
        "mood": "neutral",
        "sleep": "irregular",
    }
    proc = subprocess.run(  # noqa: S603
        [str(python), str(router), "--mas-demo", "--payload", json.dumps(payload)],
        capture_output=True,
        text=True,
        check=True,
    )
    out = json.loads(proc.stdout)
    v = out.get("validation", {})
    assert v.get("patient_to_clinician", {}).get("ok") is True
    assert v.get("clinician_to_physio", {}).get("ok") is True
    assert v.get("physio_to_patient", {}).get("ok") is True
    assert "patient" in out and "clinician" in out and "physio" in out
