from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from backend.src.mcp.echo_server import serve_in_thread


def test_mas_mcp_env_paths_with_echo_server(monkeypatch) -> None:
    # Start echo server
    srv, thread, port = serve_in_thread(0)
    try:
        base = f"http://127.0.0.1:{port}"
        # Set env to point MAS endpoints to echo
        monkeypatch.setenv("MCP_BASE_URL", base)
        monkeypatch.setenv("MCP_TOOL_PATIENT_TO_CLINICIAN_PATH", "/echo")
        monkeypatch.setenv("MCP_TOOL_CLINICIAN_TO_PHYSIO_PATH", "/echo")
        monkeypatch.setenv("MCP_TOOL_PHYSIO_TO_PATIENT_PATH", "/echo")

        root = Path(__file__).resolve().parents[2]
        python = Path(sys.executable)
        router = root / "backend" / "src" / "agents" / "router.py"

        payload = {
            "patient_id": "p_env",
            "pain_level": 4,
            "pain_desc": "lumbar",
            "mood": "neutral",
            "sleep": "regular",
        }
        proc = subprocess.run(  # noqa: S603
            [str(python), str(router), "--mas-demo", "--mas-mcp", "--payload", json.dumps(payload)],
            capture_output=True,
            text=True,
            check=True,
        )
        out = json.loads(proc.stdout)
        assert isinstance(out, dict) and "mcp_transcript" in out
        for item in out["mcp_transcript"]:
            post = item.get("post")
            # Expect a 200 status from echo endpoint
            assert isinstance(post, dict)
            assert post.get("status") == 200
    finally:
        srv.shutdown()
