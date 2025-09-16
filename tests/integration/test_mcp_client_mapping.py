import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PYTHON = Path(sys.executable)
CLIENT = ROOT / "backend" / "src" / "mcp" / "client.py"


def test_client_uses_env_defaults_when_cli_defaults():
    # When CLI args are left as defaults, client should resolve env-based paths
    env = {
        "MCP_BASE_URL": "http://127.0.0.1:9999",
        "MCP_TOOL_AIP_TO_ASD_PATH": "/custom-echo",
        # Leaving ASD->AIPer unused here
    }
    # Dry run (no send) just to check output structure; ensure no network is hit
    proc = subprocess.run(
        [
            str(PYTHON),
            str(CLIENT),
            # Intentionally provide defaults to trigger env mapping usage
            "--base-url",
            "http://localhost:3000",
            "--echo-path",
            "/echo",
            "-p",
            json.dumps({"type": "ping", "from": "test"}),
        ],
        capture_output=True,
        text=True,
        check=True,
        env={**os.environ, **env},
    )
    out = json.loads(proc.stdout)
    # Should contain validation and mapped fields
    assert "validation" in out and "mapped" in out
    # No 'post' since we didn't send
    assert "post" not in out
