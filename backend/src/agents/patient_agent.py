from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from backend.src.services.research_network_service import (
    evaluate_query_against_patient,
    fulfill_query_offline,
)


def main() -> None:
    p = argparse.ArgumentParser(description="Patient Agent (AP) offline demo")
    p.add_argument("--patient-id", required=True)
    p.add_argument("--profile", help="Path to patient profile JSON", required=True)
    p.add_argument("--query", help="Path to research query JSON", required=True)
    p.add_argument("--data", help="Path to patient data JSON (fields)", required=True)
    args = p.parse_args()

    profile: dict[str, Any] = json.loads(Path(args.profile).read_text(encoding="utf-8"))
    query: dict[str, Any] = json.loads(Path(args.query).read_text(encoding="utf-8"))
    data: dict[str, Any] = json.loads(Path(args.data).read_text(encoding="utf-8"))

    if not evaluate_query_against_patient(query, profile):
        sys.stdout.write(json.dumps({"accepted": False, "reason": "criteria_not_met"}) + "\n")
        return

    res = fulfill_query_offline(
        patient_id=args.patient_id,
        patient_profile=profile,
        query=query,
        patient_data=data,
    )
    sys.stdout.write(json.dumps({"accepted": True, "result": res}, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
