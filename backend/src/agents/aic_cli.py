from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from backend.src.services.aic_service import generate_structured_report


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate clinician weekly report (offline-first)")
    parser.add_argument("patient_id", help="Patient identifier")
    parser.add_argument("--data", type=str, default=None, help="Path to JSON file with optional input data")
    parser.add_argument("--out", type=str, default=None, help="Path to write JSON report (stdout if omitted)")
    args = parser.parse_args()

    input_data: dict[str, Any] | None = None
    if args.data:
        p = Path(args.data)
        with p.open("r", encoding="utf-8") as f:
            input_data = json.load(f)

    report = generate_structured_report(args.patient_id, input_data)

    payload = json.dumps(report, ensure_ascii=False, indent=2)
    if args.out:
        outp = Path(args.out)
        outp.parent.mkdir(parents=True, exist_ok=True)
        with outp.open("w", encoding="utf-8") as f:
            f.write(payload)
    else:
        sys.stdout.write(payload + "\n")

if __name__ == "__main__":
    main()
