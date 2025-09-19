from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PY = str((ROOT / ".venv" / "Scripts" / "python.exe").resolve())


def run_cmd(args: list[str]) -> tuple[int, str, str]:
    p = subprocess.run(args, capture_output=True, text=True)
    return p.returncode, p.stdout, p.stderr


def test_patient_agent_health_and_envelope(tmp_path: Path) -> None:
    code, out, err = run_cmd([PY, "-m", "backend.src.agents.patient_agent", "--health"])  # noqa: S603
    assert code == 0, err
    j = json.loads(out)
    assert j["from"] == "AP"
    assert j["status"] == "ok"
    assert j["ready"] is True
    assert "meta" in j and isinstance(j["meta"], dict)

    # Now run normal flow with minimal JSONs
    profile = tmp_path / "profile.json"
    profile.write_text(json.dumps({"age": 40, "conditions": ["pain"]}), encoding="utf-8")
    query = tmp_path / "query.json"
    query.write_text(json.dumps({"criteria": {"min_age": 18}}), encoding="utf-8")
    data = tmp_path / "data.json"
    data.write_text(json.dumps({"symptoms": ["back_pain"]}), encoding="utf-8")

    code, out, err = run_cmd(
        [
            PY,
            "-m",
            "backend.src.agents.patient_agent",
            "--patient-id",
            "p1",
            "--profile",
            str(profile),
            "--query",
            str(query),
            "--data",
            str(data),
        ]
    )
    assert code == 0, err
    j = json.loads(out)
    assert isinstance(j.get("ok"), bool)
    assert "meta" in j and isinstance(j["meta"], dict)
    assert "data" in j and isinstance(j["data"], dict)
    if j["ok"] is True:
        assert j["error"] is None
        assert j["data"].get("accepted") is True
        assert "result" in j["data"]
    else:
        # When criteria/consent or validation fails, we still enforce envelope shape
        assert j["data"].get("accepted") is False
        assert j.get("error") is not None


def test_aic_cli_health_and_envelope(tmp_path: Path) -> None:
    code, out, err = run_cmd([PY, "-m", "backend.src.agents.aic_cli", "--health"])  # noqa: S603
    assert code == 0, err
    j = json.loads(out)
    assert j["from"] == "AIC"
    assert j["status"] == "ok"
    assert j["ready"] is True
    assert "meta" in j and isinstance(j["meta"], dict)

    # Normal flow returns unified envelope
    code, out, err = run_cmd([PY, "-m", "backend.src.agents.aic_cli", "p1"])  # noqa: S603
    assert code == 0, err
    j = json.loads(out)
    assert j["ok"] is True
    assert j["error"] is None
    assert "meta" in j
    assert "data" in j and isinstance(j["data"], dict)
