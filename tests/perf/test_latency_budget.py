from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

# This test enforces a soft latency budget for a single MAS demo run (offline mode).
# It will be skipped automatically if the router script is not found.
# Budget: end-to-end execution (patient->clinician->physio with optional AIC disabled) < 3 seconds.

BUDGET_SECONDS = 3.0
REPO_ROOT = Path(__file__).resolve().parents[2]
ROUTER = REPO_ROOT / "backend" / "src" / "agents" / "router.py"


def test_mas_latency_budget():
    if not ROUTER.exists():  # pragma: no cover - guard
        import pytest
        pytest.skip("router script not present")

    start_payload = {"patient_id": "latency_demo", "pain_level": 4, "pain_desc": "stiffness"}
    cmd = [sys.executable, str(ROUTER), "--mas-demo"]
    t0 = time.perf_counter()
    proc = subprocess.run(cmd, input=json.dumps(start_payload).encode(), capture_output=True, check=True)  # noqa: S603
    dur = time.perf_counter() - t0
    assert dur < BUDGET_SECONDS, f"MAS demo exceeded latency budget: {dur:.2f}s >= {BUDGET_SECONDS}s\nSTDERR:{proc.stderr.decode()}"  # noqa: S101
