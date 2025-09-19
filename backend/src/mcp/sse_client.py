from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from typing import Any, AsyncIterator, Dict, Optional

import httpx

# Optional import for httpx_sse. Tests can monkeypatch module attr `connect_sse`.
try:  # pragma: no cover - exercised via tests monkeypatch
    from httpx_sse import connect_sse as _connect_sse  # type: ignore
except Exception:  # pragma: no cover - absence is acceptable (fallback used)
    _connect_sse = None  # type: ignore[assignment]

# Expose a module attribute that tests can monkeypatch
connect_sse = _connect_sse  # type: ignore[assignment]


@dataclass
class MCPEvent:
    event: str
    data: str

    def json(self) -> Any:
        try:
            return json.loads(self.data)
        except Exception:
            return {"raw": self.data}


class MCPClient:
    """
    Minimal MCP-over-SSE client for Coral.

    Contract:
    - Inputs: base_url (e.g., "http://localhost:5555"), path (e.g., "/" or "/sse"), optional bearer token
    - Behavior: Opens an SSE stream, yields events as they arrive
    - Errors: Raises httpx.HTTPError on connection issues; supports timeout and retries via caller
    - Success: Able to read at least one event or keep the stream open until cancelled
    """

    def __init__(
        self,
        base_url: str,
        path: str = "/",
        token: Optional[str] = None,
        timeout: float = 30.0,
        headers: Optional[Dict[str, str]] = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.path = path if path.startswith("/") else f"/{path}"
        self.token = token
        self.timeout = timeout
        self.headers = headers or {}
        if token and "Authorization" not in self.headers:
            self.headers["Authorization"] = f"Bearer {token}"
        # Explicitly accept SSE
        if "Accept" not in self.headers:
            self.headers["Accept"] = "text/event-stream"

    async def events(self) -> AsyncIterator[MCPEvent]:
        url = f"{self.base_url}{self.path}"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            if connect_sse is not None:
                async with connect_sse(client, "GET", url, headers=self.headers) as sse:  # type: ignore[misc]
                    async for event in sse.aiter_sse():
                        yield MCPEvent(event=event.event or "message", data=event.data or "")
                return

            # Fallback: naive SSE line reader (event: / data:) over streaming HTTP
            async with client.stream("GET", url, headers=self.headers) as resp:
                resp.raise_for_status()
                buf_event = "message"
                buf_data_lines: list[str] = []
                async for line in resp.aiter_lines():
                    if line is None:
                        continue
                    if line.startswith(":"):
                        # comment/heartbeat
                        continue
                    if not line:
                        # dispatch accumulated
                        data = "\n".join(buf_data_lines)
                        if data:
                            yield MCPEvent(event=buf_event, data=data)
                        buf_event = "message"
                        buf_data_lines = []
                        continue
                    if line.startswith("event:"):
                        buf_event = line[len("event:") :].strip() or "message"
                    elif line.startswith("data:"):
                        buf_data_lines.append(line[len("data:") :].strip())

    async def first_event(self) -> Optional[MCPEvent]:
        try:
            async for ev in self.events():
                return ev
        except httpx.HTTPError:
            return None
        return None


async def _demo(url: str, path: str, token: Optional[str], once: bool) -> None:
    client = MCPClient(url, path, token)
    if once:
        ev = await client.first_event()
        if ev:
            print(json.dumps({"event": ev.event, "data": ev.json()}, ensure_ascii=False))  # noqa: T201
        else:
            print(json.dumps({"error": "no_event"}))  # noqa: T201
        return

    async for ev in client.events():
        print(json.dumps({"event": ev.event, "data": ev.json()}, ensure_ascii=False))  # noqa: T201


def run_cli(argv: Optional[list[str]] = None) -> int:
    import argparse

    p = argparse.ArgumentParser(description="SSE MCP client (Coral)")
    p.add_argument("--url", default="http://localhost:5555", help="Base URL, e.g., http://localhost:5555")
    p.add_argument("--path", default="/", help="SSE path: '/' or '/sse' if server uses it")
    p.add_argument("--token", default=None, help="Optional bearer token")
    p.add_argument("--once", action="store_true", help="Stop after first event")
    p.add_argument("--timeout", type=float, default=30.0, help="Client timeout seconds")
    args = p.parse_args(argv)

    async def _run() -> None:
        try:
            await asyncio.wait_for(_demo(args.url, args.path, args.token, args.once), timeout=args.timeout)
        except asyncio.TimeoutError:
            print(json.dumps({"error": "timeout"}))  # noqa: T201

    asyncio.run(_run())
    return 0


if __name__ == "__main__":
    raise SystemExit(run_cli())
