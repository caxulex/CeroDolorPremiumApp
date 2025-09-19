from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PY = str((ROOT / ".venv" / "Scripts" / "python.exe").resolve())


def run_cmd(args: list[str]):
    p = subprocess.run(args, capture_output=True, text=True)
    return p.returncode, p.stdout, p.stderr


def _assert_env_ok(j: dict) -> None:
    assert isinstance(j.get("ok"), bool)
    assert "meta" in j and isinstance(j["meta"], dict)
    if j["ok"]:
        assert j.get("error") in (None, {})
        assert j.get("data") is not None
    else:
        assert j.get("error") is not None


def test_aip_envelope_smoke():
    code, out, err = run_cmd([PY, "-m", "backend.src.agents.aip", "--ping"])  # noqa: S603
    assert code == 0, err
    j = json.loads(out)
    _assert_env_ok(j)
    assert j["data"]["from"] == "AIP"


def test_asd_envelope_smoke():
    code, out, err = run_cmd([PY, "-m", "backend.src.agents.asd", "--ping"])  # noqa: S603
    assert code == 0, err
    j = json.loads(out)
    _assert_env_ok(j)
    assert j["data"]["from"] == "ASD"


def test_aiper_envelope_smoke():
    code, out, err = run_cmd([PY, "-m", "backend.src.agents.aiper", "--ping"])  # noqa: S603
    assert code == 0, err
    j = json.loads(out)
    _assert_env_ok(j)
    assert j["data"]["from"] == "AIPer"


def test_ac_envelope_smoke(tmp_path: Path):
    req = tmp_path / "ac_req.json"
    req.write_text("{}", encoding="utf-8")
    code, out, err = run_cmd([PY, "-m", "backend.src.agents.clinician_agent", "--request", str(req)])  # noqa: S603
    assert code == 0, err
    j = json.loads(out)
    _assert_env_ok(j)
    assert j["data"]["received"] is True

    # Missing request should produce ok:false envelope
    code, out, err = run_cmd([PY, "-m", "backend.src.agents.clinician_agent"])  # noqa: S603
    assert code != 0
    j = json.loads(out)
    assert j["ok"] is False
    assert j["error"]["kind"] == "missing_request"
