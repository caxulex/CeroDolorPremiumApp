import argparse
import json
import sys
from pathlib import Path
from typing import Any


def _load_payload(input_path: str | None) -> dict[str, Any]:
    if input_path:
        data = Path(input_path).read_text(encoding="utf-8")
    else:
        data = sys.stdin.read().strip()
    try:
        return json.loads(data) if data else {}
    except json.JSONDecodeError:
        return {"error": "invalid_json", "raw": data}


def main() -> None:
    parser = argparse.ArgumentParser(description="ASD agent")
    parser.add_argument("--input", "-i", help="Path to input JSON file")
    parser.add_argument("--ping", action="store_true", help="Send a ping message")
    args = parser.parse_args()

    payload: dict[str, Any] = _load_payload(args.input)
    if args.ping and not payload:
        payload = {"type": "ping"}

    out = {
        "from": "ASD",
        "type": "pong" if payload.get("type") == "ping" else "ack",
        "insights": {"patterns_detected": ["placeholder"]},
        "echo": payload,
    }
    sys.stdout.write(json.dumps(out))


if __name__ == "__main__":
    main()
