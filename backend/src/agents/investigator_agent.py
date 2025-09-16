from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from backend.src.mcp.validation import validate_research_query


def main() -> None:
    p = argparse.ArgumentParser(description="Investigator Agent (AI) offline demo")
    p.add_argument("--query", help="Path to research query JSON", required=True)
    args = p.parse_args()

    query: dict[str, Any] = json.loads(Path(args.query).read_text(encoding="utf-8"))
    errs = validate_research_query(query)
    if errs:
        sys.stdout.write(json.dumps({"ok": False, "errors": errs}, ensure_ascii=False) + "\n")
    else:
        sys.stdout.write(json.dumps({"ok": True, "query": query}, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
