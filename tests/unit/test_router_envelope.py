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


def test_router_outputs_envelope():
    code, out, err = run_cmd([PY, str(ROUTER), "--payload", "{}", "--compact-output"])  # noqa: S603
    assert code == 0, err
    j = json.loads(out)
    assert j["ok"] is True
    assert j["error"] is None
    assert "meta" in j and isinstance(j["meta"], dict)
    assert "data" in j and isinstance(j["data"], dict)
    assert "validation" in j["data"]
    assert all(k in j["data"] for k in ("aip", "asd", "aiper"))
