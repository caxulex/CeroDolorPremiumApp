"""Simple load / smoke simulation for patient cycles.

Generates synthetic patient inputs and runs orchestrated cycles to:
 - Measure latency distribution
 - Validate no exceptions under moderate load
 - Produce lightweight summary (stdout + optional JSON file)

Usage (PowerShell):
  python scripts/load_simulation.py --patients 10 --cycles 5 --output summary.json

Environment respects offline mode; no network calls expected unless flags permit.
"""
from __future__ import annotations

import argparse
import json
import random
import statistics
import time
import sys
from pathlib import Path
from typing import Any, Dict, List

# Ensure project root on sys.path for 'backend' package imports when invoked directly
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from backend.src.agents.orchestrator import run_patient_cycle, PatientInput  # type: ignore
    from backend.src.utils.logging_utils import info, warn  # type: ignore
except ModuleNotFoundError as e:  # pragma: no cover - startup diagnostic
    print(f"[FATAL] Import failure: {e}. Did you run from repository root?", file=sys.stderr)
    raise

MOODS = ["neutral", "positivo", "deprimido", "ansioso", "irritable"]
SLEEPS = ["bueno", "regular", "malo"]
DESCS = [
    "dolor lumbar suave",
    "sensación punzante en cuello",
    "rigidez moderada",
    "molestia articular leve",
    "opresión difusa",
]


def synthetic_input(pid: str, idx: int) -> Dict[str, Any]:
    # Vary pain with slight random walk to trigger trends/anomalies
    base = 4 + (hash(pid) % 3)
    level = max(0, min(10, base + random.randint(-2, 3)))
    return {
        "patient_id": pid,
        "pain_level": level,
        "pain_desc": random.choice(DESCS),
        "mood": random.choice(MOODS),
        "sleep": random.choice(SLEEPS),
    }


def run_simulation(patients: int, cycles: int, output: Path | None) -> Dict[str, Any]:
    latencies: List[float] = []
    interventions: Dict[str, int] = {}
    errors: List[str] = []

    for p in range(patients):
        pid = f"sim_patient_{p+1}"
        for c in range(cycles):
            payload = synthetic_input(pid, c)
            start = time.perf_counter()
            try:
                cycle = run_patient_cycle(payload, include_report=False)  # type: ignore[arg-type]
            except Exception as e:  # noqa: BLE001
                errors.append(f"{pid}-cycle{c+1}: {e!r}")
                continue
            latencies.append(time.perf_counter() - start)
            intr = cycle.get("aiper", {}).get("intervention_type") if isinstance(cycle.get("aiper"), dict) else None
            if isinstance(intr, str):
                interventions[intr] = interventions.get(intr, 0) + 1

    summary = {
        "patients": patients,
        "cycles_per_patient": cycles,
        "total_cycles_attempted": patients * cycles,
        "total_cycles_completed": len(latencies),
        "errors": errors,
        "latency_sec": {
            "min": round(min(latencies), 4) if latencies else None,
            "max": round(max(latencies), 4) if latencies else None,
            "mean": round(statistics.mean(latencies), 4) if latencies else None,
            "p50": round(statistics.median(latencies), 4) if latencies else None,
            "p95": round(_percentile(latencies, 95), 4) if latencies else None,
        },
        "intervention_type_counts": interventions,
    }

    info("Load simulation completed", extra={"summary": summary})
    if errors:
        warn("Errors encountered in simulation", extra={"count": len(errors)})

    if output:
        output.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        info("Summary JSON written", extra={"path": str(output)})
    return summary


def _percentile(data: List[float], pct: int) -> float:
    if not data:
        return 0.0
    if pct <= 0:
        return min(data)
    if pct >= 100:
        return max(data)
    ordered = sorted(data)
    k = (len(ordered) - 1) * (pct / 100)
    f = int(k)
    c = min(f + 1, len(ordered) - 1)
    if f == c:
        return ordered[f]
    return ordered[f] + (ordered[c] - ordered[f]) * (k - f)


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Run synthetic load simulation")
    ap.add_argument("--patients", type=int, default=5, help="Number of synthetic patients")
    ap.add_argument("--cycles", type=int, default=3, help="Cycles per patient")
    ap.add_argument("--output", type=Path, help="Optional JSON summary output path", default=None)
    return ap.parse_args()


if __name__ == "__main__":  # pragma: no cover - integration script
    args = parse_args()
    run_simulation(args.patients, args.cycles, args.output)
