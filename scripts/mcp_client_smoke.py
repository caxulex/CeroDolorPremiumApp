import os
import sys

# Allow running from repo root
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "backend"))

from src.mcp.sse_client import run_cli  # noqa: E402


if __name__ == "__main__":
    # Delegate to the SSE client's CLI; keep this thin so it's easy to call from PowerShell
    raise SystemExit(run_cli())
