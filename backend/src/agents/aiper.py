import argparse
import json
import sys
from pathlib import Path
from typing import Any


def _load_payload(input_path: str | None) -> dict[str, Any]:
    if input_path:
        data = Path(input_path).read_text(encoding="utf-8")
    else:
        try:
            if hasattr(sys.stdin, "isatty") and sys.stdin.isatty():
                return {}
        except Exception:
            return {}
        data = sys.stdin.read().strip()
    try:
        return json.loads(data) if data else {}
    except json.JSONDecodeError:
        return {"error": "invalid_json", "raw": data}


def main() -> None:
    parser = argparse.ArgumentParser(description="AIPer agent")
    parser.add_argument("--input", "-i", help="Path to input JSON file")
    parser.add_argument("--ping", action="store_true", help="Send a ping message")
    parser.add_argument("--health", action="store_true", help="Print health JSON and exit")
    args = parser.parse_args()

    if args.health:
        from backend.src.agents.base import make_meta  # type: ignore
        out = {"from": "AIPer", "status": "ok", "ready": True, "version": 1, "meta": make_meta()}
        sys.stdout.write(json.dumps(out) + "\n")
        return

    payload: dict[str, Any] = _load_payload(args.input)
    if args.ping and not payload:
        payload = {"type": "ping"}

    try:
        from backend.src.agents.base import make_meta  # type: ignore
        meta = make_meta()
    except Exception:
        meta = None
    result = {
        "from": "AIPer",
        "type": "pong" if payload.get("type") == "ping" else "ack",
        "suggestion": "Try a 5-minute guided breathing exercise.",
        "echo": payload,
    }
    env = {"ok": True, "data": result, "error": None, "meta": meta}
    sys.stdout.write(json.dumps(env))


if __name__ == "__main__":
    main()
