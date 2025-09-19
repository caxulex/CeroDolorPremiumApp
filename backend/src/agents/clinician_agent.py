from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> None:
    p = argparse.ArgumentParser(description="Clinician Agent (AC) placeholder")
    p.add_argument("--request", help="Path to clinician request JSON", required=False)
    p.add_argument("--health", action="store_true", help="Print health JSON and exit")
    args = p.parse_args()

    if args.health:
        from backend.src.agents.base import make_meta  # type: ignore
        sys.stdout.write(json.dumps({"from": "AC", "status": "ok", "ready": True, "version": 1, "meta": make_meta()}) + "\n")
        return

    if not args.request:
        try:
            from backend.src.agents.base import make_meta  # type: ignore
            meta = make_meta()
        except Exception:
            meta = None
        env = {"ok": False, "data": None, "error": {"kind": "missing_request", "message": "Use --request <path> or --health"}, "meta": meta}
        sys.stdout.write(json.dumps(env) + "\n")
        sys.exit(2)

    # For now, just echo the request; the AC would typically talk to AP
    req = json.loads(Path(args.request).read_text(encoding="utf-8"))
    try:
        from backend.src.agents.base import make_meta  # type: ignore
        meta = make_meta()
    except Exception:
        meta = None
    env = {"ok": True, "data": {"received": True, "request": req}, "error": None, "meta": meta}
    sys.stdout.write(json.dumps(env, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
