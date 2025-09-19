from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PY = str((ROOT / ".venv" / "Scripts" / "python.exe").resolve())
ROUTER = ROOT / "backend" / "src" / "agents" / "router.py"


def run_cmd(args: list[str]):
    p = subprocess.run(args, capture_output=True, text=True)
    return p.returncode, p.stdout, p.stderr


def test_router_local_chain_smoke():
    # Provide a small starting payload and run local chain path
    payload = {"patient_id": "p1", "pain_level": 4, "pain_desc": "lumbar", "mood": "ok", "sleep": "regular"}
    code, out, err = run_cmd([PY, str(ROUTER), "--payload", json.dumps(payload)])  # noqa: S603
    assert code == 0, err
    j = json.loads(out)
    # Router now returns an envelope; inspect data payload
    assert j["ok"] is True
    assert "data" in j and isinstance(j["data"], dict)
    data = j["data"]
    assert "validation" in data and "aip_to_asd" in data["validation"]
    # AIP/ASD/AIPer items are also envelopes
    assert "aip" in data and isinstance(data["aip"], dict)
    assert "asd" in data and isinstance(data["asd"], dict)
    assert "aiper" in data and isinstance(data["aiper"], dict)
