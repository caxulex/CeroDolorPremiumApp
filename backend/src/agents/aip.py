import argparse
import json
import sys
from pathlib import Path
from typing import Any


def _load_payload(input_path: str | None) -> dict[str, Any]:
    if input_path:
        data = Path(input_path).read_text(encoding="utf-8")
    else:
        # If running interactively (no pipe), avoid blocking on stdin
        try:
            if hasattr(sys.stdin, "isatty") and sys.stdin.isatty():
                return {}
        except Exception:
            # Fallback to safe default
            return {}
        data = sys.stdin.read().strip()
    try:
        return json.loads(data) if data else {}
    except json.JSONDecodeError:
        return {"error": "invalid_json", "raw": data}


def main() -> None:
    """AIP agent CLI: ping/pong or ack, stdin or file input."""
    parser = argparse.ArgumentParser(description="AIP agent")
    parser.add_argument("--input", "-i", help="Path to input JSON file")
    parser.add_argument("--ping", action="store_true", help="Send a ping message")
    parser.add_argument("--health", action="store_true", help="Print health JSON and exit")
    args = parser.parse_args()

    if args.health:
        from backend.src.agents.base import make_meta  # type: ignore
        out = {
            "from": "AIP",
            "status": "ok",
            "ready": True,
            "version": 1,
            "meta": make_meta(),
        }
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

    # Handle invalid JSON case
    if isinstance(payload, dict) and payload.get("error") == "invalid_json":
        env = {"ok": False, "data": None, "error": {"kind": "invalid_input", "message": "invalid_json"}, "meta": meta}
        sys.stdout.write(json.dumps(env))
        return

    # Extract pain info if present
    level = None
    desc = None
    mood = None
    sleep = None
    if isinstance(payload, dict):
        # Flatten common fields
        level = payload.get("pain_level") or payload.get("level")
        desc = payload.get("pain_desc") or payload.get("description")
        mood = payload.get("mood")
        sleep = payload.get("sleep")
        # Or nested pain object
        if level is None and isinstance(payload.get("pain"), dict):
            p = payload.get("pain") or {}
            level = p.get("level") or p.get("value")
            desc = desc or p.get("description")

    severity = None
    if isinstance(level, (int, float)):
        iv = int(level)
        if iv <= 3:
            severity = "leve"
        elif iv <= 6:
            severity = "moderado"
        else:
            severity = "alto"

    result: dict[str, Any] = {
        "from": "AIP",
        "type": "pong" if payload.get("type") == "ping" else "ack",
        "echo": payload,
    }
    if severity is not None and isinstance(level, (int, float)):
        pain_obj = {"level": int(level), "severity": severity}
        if isinstance(desc, str) and desc:
            pain_obj["description"] = desc
        result["pain"] = pain_obj
    if isinstance(mood, str) and mood:
        result["mood"] = mood
    if isinstance(sleep, str) and sleep:
        result["sleep"] = sleep

    env = {"ok": True, "data": result, "error": None, "meta": meta}
    sys.stdout.write(json.dumps(env))


if __name__ == "__main__":
    main()
