from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

BUDGET_SECONDS = 3.5  # Slightly higher to account for AIC report generation
REPO_ROOT = Path(__file__).resolve().parents[2]
ROUTER = REPO_ROOT / "backend" / "src" / "agents" / "router.py"


def test_mas_aic_latency_budget():
    if not ROUTER.exists():  # pragma: no cover - guard
        import pytest
        pytest.skip("router script not present")

    start_payload = {"patient_id": "latency_aic_demo", "pain_level": 6, "pain_desc": "fatiga"}
    cmd = [sys.executable, str(ROUTER), "--mas-demo", "--include-aic"]
    t0 = time.perf_counter()
    proc = subprocess.run(cmd, input=json.dumps(start_payload).encode(), capture_output=True, check=True)  # noqa: S603
    dur = time.perf_counter() - t0
    assert dur < BUDGET_SECONDS, f"MAS demo with AIC exceeded latency budget: {dur:.2f}s >= {BUDGET_SECONDS}s\nSTDERR:{proc.stderr.decode()}"  # noqa: S101
