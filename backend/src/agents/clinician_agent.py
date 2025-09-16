from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> None:
    p = argparse.ArgumentParser(description="Clinician Agent (AC) placeholder")
    p.add_argument("--request", help="Path to clinician request JSON", required=True)
    args = p.parse_args()

    # For now, just echo the request; the AC would typically talk to AP
    req = json.loads(Path(args.request).read_text(encoding="utf-8"))
    sys.stdout.write(json.dumps({"received": True, "request": req}, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
