import json
import subprocess
import sys
import time
from pathlib import Path

import pytest

# Paths
ROOT = Path(__file__).resolve().parents[2]
PYTHON = Path(sys.executable)
ECHO_SERVER = ROOT / "backend" / "src" / "mcp" / "echo_server.py"
MCP_CLIENT = ROOT / "backend" / "src" / "mcp" / "client.py"


@pytest.mark.integration
def test_mcp_ping_pong_echo_server():
    # Start echo server on ephemeral port (0)
    # We run it as a Python module with --port 0 to auto-bind, then read stdout is tricky.
    # Instead, import serve_in_thread for stable tests.
    import importlib.util

    spec = importlib.util.spec_from_file_location("echo_server", ECHO_SERVER)
    module = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    assert spec and spec.loader
    spec.loader.exec_module(module)  # type: ignore[union-attr]

    httpd, thread, bound_port = module.serve_in_thread(0)

    try:
        # Give server a brief moment
        time.sleep(0.05)

        # Probe health
        probe = subprocess.run(
            [
                str(PYTHON),
                str(MCP_CLIENT),
                "--base-url",
                f"http://127.0.0.1:{bound_port}",
                "--health-path",
                "/health",
                "--probe",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        probe_json = json.loads(probe.stdout)
        assert probe_json.get("probe", {}).get("status") == 200

        # Send mapped payload
        send = subprocess.run(
            [
                str(PYTHON),
                str(MCP_CLIENT),
                "--base-url",
                f"http://127.0.0.1:{bound_port}",
                "--echo-path",
                "/echo",
                "--send",
                "-p",
                json.dumps({"type": "ping", "from": "test"}),
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        send_json = json.loads(send.stdout)
        post = send_json.get("post", {})
        assert post.get("status") == 200
        # One of json/text should be present; for json ensure received payload exists
        if "json" in post:
            assert post["json"].get("ok") is True
            assert post["json"].get("received", {}).get("message_type") == "pain_submission"
        else:
            assert "text" in post
    finally:
        httpd.shutdown()
        httpd.server_close()
        thread.join(timeout=1)
