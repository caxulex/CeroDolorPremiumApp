import asyncio
import json
from typing import Any

import pytest

from backend.src.mcp.sse_client import MCPClient


class _FakeEvent:
    def __init__(self, event: str, data: str) -> None:
        self.event = event
        self.data = data


class _FakeSSE:
    def __init__(self, events: list[_FakeEvent]) -> None:
        self._events = events

    async def __aenter__(self) -> "_FakeSSE":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:  # noqa: ANN001
        return None

    async def aiter_sse(self):  # noqa: ANN201 - behaves like async generator
        for e in self._events:
            yield e


class _FakeAsyncClient:
    def __init__(self, *a: Any, **k: Any) -> None:  # noqa: ANN001, ANN401
        pass

    async def __aenter__(self) -> "_FakeAsyncClient":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:  # noqa: ANN001
        return None


@pytest.mark.asyncio
async def test_first_event_json(monkeypatch: pytest.MonkeyPatch) -> None:
    # Patch connect_sse and httpx.AsyncClient used inside MCPClient.events
    import backend.src.mcp.sse_client as ssec

    fake_payload = {"hello": "world"}

    def _fake_connect(client, method, url, headers=None):  # noqa: ANN001
        return _FakeSSE([_FakeEvent("message", json.dumps(fake_payload))])

    monkeypatch.setattr(ssec, "httpx", type("X", (), {"AsyncClient": _FakeAsyncClient}))
    monkeypatch.setattr(ssec, "connect_sse", _fake_connect)

    c = MCPClient("http://localhost:5555")
    ev = await c.first_event()
    assert ev is not None
    assert ev.event == "message"
    assert ev.json() == fake_payload


@pytest.mark.asyncio
async def test_events_stream_multiple(monkeypatch: pytest.MonkeyPatch) -> None:
    import backend.src.mcp.sse_client as ssec

    seq = [
        _FakeEvent("init", "{}"),
        _FakeEvent("notice", json.dumps({"a": 1})),
        _FakeEvent("chunk", "not-json"),
    ]

    def _fake_connect(client, method, url, headers=None):  # noqa: ANN001
        return _FakeSSE(seq)

    monkeypatch.setattr(ssec, "httpx", type("X", (), {"AsyncClient": _FakeAsyncClient}))
    monkeypatch.setattr(ssec, "connect_sse", _fake_connect)

    c = MCPClient("http://localhost:5555")
    got = []
    async for ev in c.events():
        got.append((ev.event, ev.json()))
    assert got[0][0] == "init" and got[0][1] == {}
    assert got[1][0] == "notice" and got[1][1] == {"a": 1}
    assert got[2][0] == "chunk" and "raw" in got[2][1]
