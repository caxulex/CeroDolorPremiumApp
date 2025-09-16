import argparse
import json
import os
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from jsonschema import Draft7Validator

# Paths
BACKEND = Path(__file__).resolve().parents[2]  # backend/src/mcp/ -> backend/
CONTRACTS = BACKEND.parent / "specs" / "001-description-esta-secci" / "contracts"


def _utc_iso() -> str:
    return datetime.now(UTC).isoformat()


def _load_schema(path: Path) -> Draft7Validator:
    schema = json.loads(path.read_text(encoding="utf-8"))
    return Draft7Validator(schema)


def _validate(obj: dict[str, Any], validator: Draft7Validator) -> tuple[bool, str | None]:
    errors = sorted(validator.iter_errors(obj), key=lambda e: e.path)
    if errors:
        return False, errors[0].message
    return True, None


def _to_aip_to_asd(start: dict[str, Any]) -> dict[str, Any]:
    pain = {
        "level": int(start.get("pain_level", 5)),
        "description": start.get("pain_desc", "placeholder"),
        "mood": start.get("mood", "neutral"),
        "sleep_quality": start.get("sleep", "desconocido"),
    }
    return {
        "message_type": "pain_submission",
        "patient_id": start.get("patient_id", "demo_patient"),
        "timestamp": _utc_iso(),
        "pain_data": pain,
    }


def _http_get(url: str, timeout: float = 5.0) -> dict[str, Any]:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:  # Guard against file: and others (ruff S310)
        return {"error": "InvalidURLScheme", "reason": f"scheme '{parsed.scheme}' not allowed"}
    req = Request(url, method="GET")  # noqa: S310 (scheme validated above)
    try:
        with urlopen(req, timeout=timeout) as resp:  # noqa: S310 (scheme validated above)
            data = resp.read().decode()
            try:
                return {"status": resp.status, "json": json.loads(data)}
            except json.JSONDecodeError:
                return {"status": resp.status, "text": data}
    except HTTPError as e:  # pragma: no cover - network optional
        return {"error": f"HTTPError {e.code}", "reason": str(e)}
    except URLError as e:  # pragma: no cover - network optional
        return {"error": "URLError", "reason": str(e.reason)}


def _http_post(url: str, payload: dict[str, Any], timeout: float = 5.0) -> dict[str, Any]:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:  # Guard against file: and others (ruff S310)
        return {"error": "InvalidURLScheme", "reason": f"scheme '{parsed.scheme}' not allowed"}
    body = json.dumps(payload).encode()
    req = Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")  # noqa: S310 (scheme validated above)
    try:
        with urlopen(req, timeout=timeout) as resp:  # noqa: S310 (scheme validated above)
            data = resp.read().decode()
            try:
                return {"status": resp.status, "json": json.loads(data)}
            except json.JSONDecodeError:
                return {"status": resp.status, "text": data}
    except HTTPError as e:  # pragma: no cover - network optional
        return {"error": f"HTTPError {e.code}", "reason": str(e)}
    except URLError as e:  # pragma: no cover - network optional
        return {"error": "URLError", "reason": str(e.reason)}


def main() -> None:
    parser = argparse.ArgumentParser(description="MCP client shim with contract validation")
    parser.add_argument("--base-url", default="http://localhost:3000", help="Base URL of the MCP server/inspector")
    parser.add_argument("--health-path", default="/health", help="Relative health endpoint path")
    parser.add_argument("--echo-path", default="/echo", help="Relative echo endpoint path (adjust to your server)")
    parser.add_argument("--probe", action="store_true", help="Only probe health endpoint and exit")
    parser.add_argument("--payload", "-p", help="Inline JSON payload to start with (for mapping)")
    parser.add_argument("--payload-file", "-f", help="Path to a JSON file for the starting payload")
    parser.add_argument("--send", action="store_true", help="POST the mapped payload to base-url + echo-path")
    args = parser.parse_args()

    # Resolve env-based defaults only when CLI values are still default literals
    default_base = "http://localhost:3000"
    default_echo = "/echo"
    base = (
        args.base_url if args.base_url != default_base else os.getenv("MCP_BASE_URL", default_base)
    ).rstrip("/")
    echo_path = (
        args.echo_path if args.echo_path != default_echo else os.getenv("MCP_TOOL_AIP_TO_ASD_PATH", default_echo)
    )
    health_path = args.health_path  # keep as provided/default; env mapping doesn't override

    if args.probe:
        probe_id = str(uuid.uuid4())
        ts = datetime.now(UTC).isoformat()
        t0 = time.perf_counter()
        res = _http_get(base + health_path)
        dur_ms = int((time.perf_counter() - t0) * 1000)
        print(json.dumps({"id": probe_id, "ts": ts, "duration_ms": dur_ms, "probe": res}, indent=2))  # noqa: T201
        return

    # Prepare start payload
    if args.payload_file:
        start = json.loads(Path(args.payload_file).read_text(encoding="utf-8"))
    else:
        start = json.loads(args.payload) if args.payload else {"type": "ping", "from": "mcp-client"}

    # Build and validate contract payload
    mapped = _to_aip_to_asd(start)
    v1 = _load_schema(CONTRACTS / "aip_to_asd.json")
    ok, err = _validate(mapped, v1)

    out: dict[str, Any] = {
        "id": str(uuid.uuid4()),
        "ts": datetime.now(UTC).isoformat(),
        "validation": {"aip_to_asd": {"ok": ok, "error": err}},
        "mapped": mapped,
    }

    if args.send:
        t0 = time.perf_counter()
        out["post"] = _http_post(base + echo_path, mapped)
        out["duration_ms"] = int((time.perf_counter() - t0) * 1000)
    else:
        out["note"] = "Dry run. Use --send to POST to the server."

    print(json.dumps(out, indent=2))  # noqa: T201


if __name__ == "__main__":
    main()
