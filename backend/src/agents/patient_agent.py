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
    # Make flags optional to allow --health without noise; we'll validate manually below
    p.add_argument("--patient-id", required=False)
    p.add_argument("--profile", help="Path to patient profile JSON", required=False)
    p.add_argument("--query", help="Path to research query JSON", required=False)
    p.add_argument("--data", help="Path to patient data JSON (fields)", required=False)
    p.add_argument("--health", action="store_true", help="Print health JSON and exit")
    args = p.parse_args()

    if args.health:
        from backend.src.agents.base import make_meta  # type: ignore
        sys.stdout.write(json.dumps({"from": "AP", "status": "ok", "ready": True, "version": 1, "meta": make_meta()}) + "\n")
        return

    # Validate required flags when not in health mode
    missing = []
    if not args.patient_id:
        missing.append("--patient-id")
    if not args.profile:
        missing.append("--profile")
    if not args.query:
        missing.append("--query")
    if not args.data:
        missing.append("--data")
    if missing:
        p.error(f"the following arguments are required (unless --health is provided): {' '.join(missing)}")

    profile: dict[str, Any] = json.loads(Path(args.profile).read_text(encoding="utf-8"))
    query: dict[str, Any] = json.loads(Path(args.query).read_text(encoding="utf-8"))
    data: dict[str, Any] = json.loads(Path(args.data).read_text(encoding="utf-8"))
    from backend.src.agents.base import make_meta  # type: ignore

    if not evaluate_query_against_patient(query, profile):
        env = {
            "ok": False,
            "data": {"accepted": False, "reason": "criteria_not_met"},
            "error": {"kind": "criteria", "message": "criteria_not_met"},
            "meta": make_meta(),
        }
        sys.stdout.write(json.dumps(env, ensure_ascii=False) + "\n")
        return

    res = fulfill_query_offline(
        patient_id=args.patient_id,
        patient_profile=profile,
        query=query,
        patient_data=data,
    )
    if isinstance(res, dict) and res.get("error"):
        env_err = {
            "ok": False,
            "data": {"accepted": False},
            "error": res.get("error"),
            "meta": make_meta(),
        }
        sys.stdout.write(json.dumps(env_err, ensure_ascii=False) + "\n")
    else:
        env_ok = {"ok": True, "data": {"accepted": True, "result": res}, "error": None, "meta": make_meta()}
        sys.stdout.write(json.dumps(env_ok, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
