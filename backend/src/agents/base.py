from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Mapping, Protocol
from datetime import datetime, timezone
import secrets


@dataclass(frozen=True)
class AgentRequest:
    prompt: str
    context: Mapping[str, Any] | None = None


@dataclass(frozen=True)
class AgentResponse:
    text: str
    raw: Dict[str, Any] | None = None
    usage: Dict[str, Any] | None = None


class Agent(Protocol):
    def ask(self, prompt: str) -> Dict[str, Any]:
        ...

    def reset(self) -> None:
        ...

    def health(self) -> Dict[str, Any]:
        ...


def make_meta(version: int = 1) -> Dict[str, Any]:
    """Create a minimal meta envelope with timestamp and trace id."""
    return {
        "ts": datetime.now(timezone.utc).isoformat(),
        "trace_id": secrets.token_hex(8),
        "version": version,
    }


def error_envelope(kind: str, message: str, *, meta_version: int = 1) -> Dict[str, Any]:
    return {"error": kind, "message": message, "meta": make_meta(meta_version)}


__all__ = [
    "Agent",
    "AgentRequest",
    "AgentResponse",
    "make_meta",
    "error_envelope",
]
