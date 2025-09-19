from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from backend.src.services.aic_service import generate_structured_report


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate clinician weekly report (offline-first)")
    # Make positional optional to allow --health without noise; validate manually below
    parser.add_argument("patient_id", nargs="?", help="Patient identifier")
    parser.add_argument("--data", type=str, default=None, help="Path to JSON file with optional input data")
    parser.add_argument("--out", type=str, default=None, help="Path to write JSON report (stdout if omitted)")
    parser.add_argument("--health", action="store_true", help="Print health JSON and exit")
    args = parser.parse_args()

    if args.health:
        try:
            from backend.src.agents.base import make_meta  # type: ignore
            meta = make_meta()
        except Exception:
            meta = None
        payload = {"from": "AIC", "status": "ok", "ready": True, "version": 1}
        if meta:
            payload["meta"] = meta
        sys.stdout.write(json.dumps(payload) + "\n")
        return

    if not args.patient_id:
        parser.error("the following arguments are required (unless --health is provided): patient_id")

    input_data: dict[str, Any] | None = None
    if args.data:
        p = Path(args.data)
        with p.open("r", encoding="utf-8") as f:
            input_data = json.load(f)

    report = generate_structured_report(args.patient_id, input_data)

    # Unified envelope
    try:
        from backend.src.agents.base import make_meta  # type: ignore
        meta = make_meta()
    except Exception:
        meta = None
    envelope = {"ok": True, "data": report, "error": None, "meta": meta}
    payload = json.dumps(envelope, ensure_ascii=False, indent=2)
    if args.out:
        outp = Path(args.out)
        outp.parent.mkdir(parents=True, exist_ok=True)
        with outp.open("w", encoding="utf-8") as f:
            f.write(payload)
    else:
        sys.stdout.write(payload + "\n")

if __name__ == "__main__":
    main()
