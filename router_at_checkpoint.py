import argparse
import json
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

# Ensure repository root is on sys.path when running as a script
_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from backend.src.mcp.mapping import resolve_tool_paths  # noqa: E402
from backend.src.mcp.validation import (  # noqa: E402
    validate_aip_to_asd,
    validate_asd_to_aiper,
    validate_clinician_report,
    validate_clinician_to_physio,
    validate_patient_to_clinician,
    validate_physio_to_patient,
)
from backend.src.services.aic_service import generate_structured_report  # noqa: E402

BACKEND = Path(__file__).resolve().parents[2]  # backend/src/agents/ -> backend/
AIP = BACKEND / "src" / "agents" / "aip.py"
ASD = BACKEND / "src" / "agents" / "asd.py"
AIPER = BACKEND / "src" / "agents" / "aiper.py"
MCP_CLIENT = BACKEND / "src" / "mcp" / "client.py"
CONTRACTS = BACKEND.parent / "specs" / "001-description-esta-secci" / "contracts"


def run_agent(path: Path, payload: dict) -> dict:
    proc = subprocess.run(  # noqa: S603
        [sys.executable, str(path)],
        input=json.dumps(payload).encode(),
        capture_output=True,
        check=True,
    )
    return json.loads(proc.stdout.decode() or "{}")


def run_mcp_client(
    payload: dict[str, Any],
    base_url: str,
    echo_path: str,
    health_path: str,
    *,
    send: bool = False,
) -> dict[str, Any]:
    args = [
        sys.executable,
        str(MCP_CLIENT),
        "--base-url",
        base_url,
        "--health-path",
        health_path,
        "--echo-path",
        echo_path,
        "--payload",
        json.dumps(payload),
    ]
    if send:
        args.append("--send")
    try:
        proc = subprocess.run(args, capture_output=True, check=True)  # noqa: S603
        out = proc.stdout.decode() or "{}"
        return json.loads(out)
    except subprocess.CalledProcessError as e:
        return {
            "error": "mcp_client_failed",
            "code": e.returncode,
            "stdout": (e.stdout or b"").decode(errors="ignore"),
            "stderr": (e.stderr or b"").decode(errors="ignore"),
        }


def _utc_iso() -> str:
    return datetime.now(UTC).isoformat()


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



def _to_aip_to_asd(start: dict[str, Any]) -> dict[str, Any]:
    # Build a contract-compliant payload from provided start data (fallbacks for demo)
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


def _to_asd_to_aiper(patient_id: str, insights_obj: dict[str, Any] | None) -> dict[str, Any]:
    patterns = None
    if isinstance(insights_obj, dict):
        val = insights_obj.get("patterns_detected")
        if isinstance(val, list) and all(isinstance(x, str) for x in val):
            patterns = val
    if not patterns:
        patterns = ["placeholder"]
    return {
        "message_type": "insights",
        "patient_id": patient_id,
        "timestamp": _utc_iso(),
        "insights": {
            "patterns_detected": patterns,
        },
    }


def _ok_err_from_errors(errors: list[str]) -> tuple[bool, str | None]:
    return (len(errors) == 0, None if not errors else errors[0])


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Router demo: AIP -> ASD -> AIPer; MAS demo: Patient -> Clinician -> Physio",
    )
    parser.add_argument("--payload", "-p", help="Inline JSON payload to start with")
    parser.add_argument("--payload-file", "-f", help="Path to a JSON file for the starting payload")
    parser.add_argument("--mcp", action="store_true", help="Use MCP client shim instead of local subprocess agents")
    parser.add_argument("--mcp-base-url", default="http://localhost:3000", help="Base URL for MCP server/inspector")
    parser.add_argument("--mcp-echo-path", default="/echo", help="Echo/tool endpoint path for POST")
    parser.add_argument("--mcp-health-path", default="/health", help="Health endpoint path for GET")
    parser.add_argument("--mcp-send", action="store_true", help="When using --mcp, POST mapped payload to server")
    parser.add_argument("--mas-demo", action="store_true", help="Run minimal MAS flow (Patient->Clinician->Physio) locally")
    parser.add_argument("--mas-mcp", action="store_true", help="When used with --mas-demo, POST MAS messages via MCP echo")
    parser.add_argument("--include-aic", action="store_true", help="Include clinician AIC report in output (MAS/local only)")
    return parser.parse_args()


def _load_start_payload(args: argparse.Namespace) -> dict[str, Any]:
    if args.payload_file:
        return json.loads(Path(args.payload_file).read_text(encoding="utf-8"))
    return json.loads(args.payload) if args.payload else {"type": "ping", "from": "router"}


def _run_mcp_mode(*, args: argparse.Namespace, aip_to_asd: dict[str, Any], v1_ok: bool, v1_err: str | None) -> None:
    # Use MCP client shim instead of local agents
    # Resolve env-based defaults only when CLI values are still default literals
    paths = resolve_tool_paths()
    base_url = args.mcp_base_url if args.mcp_base_url != "http://localhost:3000" else paths.base_url
    echo_path = args.mcp_echo_path if args.mcp_echo_path != "/echo" else paths.aip_to_asd_path
    # Keep health default unless CLI override provided (env default is fine)
    health_path = args.mcp_health_path

    mcp_res = run_mcp_client(
        payload=aip_to_asd,
        base_url=base_url,
        echo_path=echo_path,
        health_path=health_path,
        send=bool(args.mcp_send),
    )
    print(  # noqa: T201
        json.dumps(
            {
                "validation": {
                    "aip_to_asd": {"ok": v1_ok, "error": v1_err},
                },
                "mcp": mcp_res,
            },
            indent=2,
        ),
    )


def _run_mas_demo(args: argparse.Namespace, start: dict[str, Any]) -> None:  # noqa: C901, PLR0915
        patient_msg = {
            "message_type": "patient_report",
            "patient_id": start.get("patient_id", "demo_patient"),
            "timestamp": _utc_iso(),
            "patient_report": {
                "pain_level": int(start.get("pain_level", 5)),
                "description": start.get("pain_desc", "placeholder"),
                "mood": start.get("mood", "neutral"),
                "sleep_quality": start.get("sleep", "desconocido"),
            },
        }
        m1_ok, m1_err = _ok_err_from_errors(validate_patient_to_clinician(patient_msg))

        # Clinician stub: turn patient report into a clinical_request with a goal and basic constraints
        clinician_msg = {
            "message_type": "clinical_request",
            "patient_id": patient_msg["patient_id"],
            "timestamp": _utc_iso(),
            "clinical_request": {
                "goal": "reduce_pain_and_increase_mobility",
                "constraints": [
                    "avoid_overexertion",
                    f"pain_level<= {patient_msg['patient_report']['pain_level']}",
                ],
                "insights": ["daytime_pain_spikes", "sleep_variability"],
            },
        }
        m2_ok, m2_err = _ok_err_from_errors(validate_clinician_to_physio(clinician_msg))

        # Physio stub: produce a simple exercise plan
        physio_msg = {
            "message_type": "exercise_plan",
            "patient_id": clinician_msg["patient_id"],
            "timestamp": _utc_iso(),
            "exercise_plan": {
                "items": [
                    {
                        "name": "gentle_stretching",
                        "repetitions": 5,
                        "frequency_per_day": 2,
                        "notes": "slow, controlled",
                    },
                    {
                        "name": "short_walk",
                        "repetitions": 1,
                        "frequency_per_day": 1,
                        "notes": "5-10 minutes",
                    },
                ],
            },
        }
        m3_ok, m3_err = _ok_err_from_errors(validate_physio_to_patient(physio_msg))

        out_obj: dict[str, Any] = {
            "validation": {
                "patient_to_clinician": {"ok": m1_ok, "error": m1_err},
                "clinician_to_physio": {"ok": m2_ok, "error": m2_err},
                "physio_to_patient": {"ok": m3_ok, "error": m3_err},
            },
            "patient": patient_msg,
            "clinician": clinician_msg,
            "physio": physio_msg,
        }

        # Optional: Generate AIC clinician report and validate against schema
        if args.include_aic:
            try:
                t0_aic = time.perf_counter()
                report = generate_structured_report(
                    clinician_msg["patient_id"],
                    {
                        "patient": patient_msg,
                        "clinician": clinician_msg,
                        "physio": physio_msg,
                    },
                )
                aic_dur_ms = int((time.perf_counter() - t0_aic) * 1000)
                aic_errs = validate_clinician_report(report)
                out_obj["validation"]["clinician_report"] = {
                    "ok": len(aic_errs) == 0,
                    "error": None if not aic_errs else aic_errs[0],
                }
                out_obj["aic_report"] = report
                out_obj["aic_meta"] = {"duration_ms": aic_dur_ms}
            except Exception as e:  # noqa: BLE001 - defensive guard for demo path
                out_obj["validation"]["clinician_report"] = {
                    "ok": False,
                    "error": f"aic_failed: {e}",
                }

        if args.mas_mcp:
            # Use MCP client shim to POST each message to echo endpoint
            paths = resolve_tool_paths()
            base_url = paths.base_url
            health_path = "/health"
            # Prefer MAS-specific paths when available, fallback to echo (aip_to_asd_path)
            mas_paths = {
                "patient": paths.patient_to_clinician_path or paths.aip_to_asd_path,
                "clinician": paths.clinician_to_physio_path or paths.aip_to_asd_path,
                "physio": paths.physio_to_patient_path or paths.aip_to_asd_path,
            }
            transcript: list[dict[str, Any]] = []

            def _validate_msg(label: str, msg: dict[str, Any]) -> tuple[bool, str | None]:
                if label == "patient":
                    errs = validate_patient_to_clinician(msg)
                elif label == "clinician":
                    errs = validate_clinician_to_physio(msg)
                else:
                    errs = validate_physio_to_patient(msg)
                return (len(errs) == 0, None if not errs else errs[0])

            for label, msg in ("patient", patient_msg), ("clinician", clinician_msg), ("physio", physio_msg):
                ok, err = _validate_msg(label, msg)
                echo_path = mas_paths[label]
                echo_url = base_url.rstrip("/") + "/" + echo_path.lstrip("/")
                t0 = time.perf_counter()
                post_res = _http_post(echo_url, msg)
                dur_ms = int((time.perf_counter() - t0) * 1000)
                transcript.append(
                    {
                        "label": label,
                        "ts": _utc_iso(),
                        "duration_ms": dur_ms,
                        "validation": {"ok": ok, "error": err},
                        "post": post_res,
                        "health_path": health_path,
                        "echo_path": echo_path,
                    },
                )
            out_obj["mcp_transcript"] = transcript

        # If we have both an AIC report and a MAS MCP transcript, enrich highlights and attach an AIC transcript item
        if args.include_aic and out_obj.get("aic_report") and out_obj.get("mcp_transcript"):
            try:
                aic: dict[str, Any] = out_obj["aic_report"]  # type: ignore[assignment]
                highlights = list(aic.get("highlights", []))
                # Summarize per-hop timings/validation into at most 3 extra highlights
                add_lines: list[str] = []
                for item in out_obj["mcp_transcript"][-3:]:  # type: ignore[index]
                    lbl = item.get("label", "?")
                    dur = item.get("duration_ms")
                    val = item.get("validation", {}) or {}
                    ok = val.get("ok")
                    err = val.get("error")
                    if ok is True:
                        add_lines.append(f"MAS {lbl}: ok en {dur} ms")
                    elif ok is False and err:
                        add_lines.append(f"MAS {lbl}: error '{err}' en {dur} ms")
                    else:
                        add_lines.append(f"MAS {lbl}: validación desconocida en {dur} ms")
                # Respect schema's maxItems=10 for highlights
                remaining = max(0, 10 - len(highlights))
                if remaining > 0:
                    highlights.extend(add_lines[:remaining])
                aic["highlights"] = highlights

                # Append an AIC summary entry to transcript for one-glance view
                aic_ms = int(out_obj.get("aic_meta", {}).get("duration_ms", 0))  # type: ignore[call-arg]
                out_obj["mcp_transcript"].append(  # type: ignore[union-attr]
                    {
                        "label": "aic_report",
                        "ts": _utc_iso(),
                        "duration_ms": aic_ms,
                        "validation": out_obj["validation"].get("clinician_report", {}),
                        "summary": {"highlights": highlights[:3]},
                    },
                )
            except Exception:  # noqa: BLE001, S110
                # Non-fatal enrichment failure should not break main output
                pass

        print(json.dumps(out_obj, indent=2))  # noqa: T201


def _run_local_chain(*, aip_to_asd: dict[str, Any], v1_ok: bool, v1_err: str | None) -> None:
    # Default: local subprocess agents
    r1 = run_agent(AIP, aip_to_asd)

    asd_to_aiper = _to_asd_to_aiper(aip_to_asd["patient_id"], r1.get("insights"))
    v2_ok, v2_err = _ok_err_from_errors(validate_asd_to_aiper(asd_to_aiper))

    r2 = run_agent(ASD, asd_to_aiper)
    r3 = run_agent(AIPER, asd_to_aiper)

    print(  # noqa: T201
        json.dumps(
            {
                "validation": {
                    "aip_to_asd": {"ok": v1_ok, "error": v1_err},
                    "asd_to_aiper": {"ok": v2_ok, "error": v2_err},
                },
                "aip": r1,
                "asd": r2,
                "aiper": r3,
            },
            indent=2,
        ),
    )


def main() -> None:
    args = _parse_args()
    start = _load_start_payload(args)

    # Map to contracts and validate
    aip_to_asd = _to_aip_to_asd(start)
    v1_ok, v1_err = _ok_err_from_errors(validate_aip_to_asd(aip_to_asd))

    if args.mcp:
        _run_mcp_mode(args=args, aip_to_asd=aip_to_asd, v1_ok=v1_ok, v1_err=v1_err)
        return

    if args.mas_demo:
        _run_mas_demo(args, start)
        return

    _run_local_chain(aip_to_asd=aip_to_asd, v1_ok=v1_ok, v1_err=v1_err)

    # Default: local subprocess agents
    r1 = run_agent(AIP, aip_to_asd)

    asd_to_aiper = _to_asd_to_aiper(aip_to_asd["patient_id"], r1.get("insights"))
    v2_ok, v2_err = _ok_err_from_errors(validate_asd_to_aiper(asd_to_aiper))

    r2 = run_agent(ASD, asd_to_aiper)
    r3 = run_agent(AIPER, asd_to_aiper)

    print(  # noqa: T201
        json.dumps(
            {
                "validation": {
                    "aip_to_asd": {"ok": v1_ok, "error": v1_err},
                    "asd_to_aiper": {"ok": v2_ok, "error": v2_err},
                },
                "aip": r1,
                "asd": r2,
                "aiper": r3,
            },
            indent=2,
        ),
    )


if __name__ == "__main__":
    main()
