from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from backend.src.mcp.echo_server import serve_in_thread


def test_router_mas_mcp_with_echo_server() -> None:
    srv, thread, port = serve_in_thread(0)
    try:
        root = Path(__file__).resolve().parents[2]
        python = Path(sys.executable)
        router = root / "backend" / "src" / "agents" / "router.py"

        payload = {
            "patient_id": "p_demo",
            "pain_level": 5,
            "pain_desc": "dolor lumbar",
            "mood": "neutral",
            "sleep": "ok",
        }
        # Base URL is resolved via mapping/env inside router->client; we only validate transcript shape.
        proc = subprocess.run(  # noqa: S603
            [str(python), str(router), "--mas-demo", "--mas-mcp", "--payload", json.dumps(payload)],
            capture_output=True,
            text=True,
            check=True,
        )
        out = json.loads(proc.stdout)
        assert isinstance(out, dict)
        assert out.get("mcp_transcript") and isinstance(out["mcp_transcript"], list)
        # Each transcript item should include a post response dict, duration, and validation
        for item in out["mcp_transcript"]:
            assert isinstance(item, dict)
            assert "post" in item
            assert "duration_ms" in item and isinstance(item["duration_ms"], int)
            assert "validation" in item and isinstance(item["validation"], dict)
    finally:
        srv.shutdown()