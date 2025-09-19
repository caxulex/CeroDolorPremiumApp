"""Lightweight structured logging wrapper.

Provides consistent logging across the app without pulling in heavy dependencies.
Can later be swapped or extended for JSON logging, external aggregation, etc.
"""
from __future__ import annotations

import json
import os
import sys
import time
from dataclasses import asdict, is_dataclass
from typing import Any, Mapping, MutableMapping, Optional

_LOG_LEVELS = {"DEBUG": 10, "INFO": 20, "WARN": 30, "ERROR": 40}
_DEFAULT_LEVEL = os.getenv("CERODOLOR_LOG_LEVEL", "INFO").upper()
_CURRENT_LEVEL = _LOG_LEVELS.get(_DEFAULT_LEVEL, 20)
_JSON_MODE = os.getenv("CERODOLOR_LOG_JSON", "0") in {"1", "true", "True"}


def _level_enabled(level: str) -> bool:
    return _LOG_LEVELS[level] >= _CURRENT_LEVEL


def _serialize(obj: Any) -> Any:
    # is_dataclass returns True for both instances and dataclass types; only serialize instances
    if is_dataclass(obj) and not isinstance(obj, type):  # type: ignore[arg-type]
        try:
            return asdict(obj)  # type: ignore[arg-type]
        except Exception:
            return repr(obj)
    if isinstance(obj, (list, tuple)):
        return [_serialize(x) for x in obj]
    if isinstance(obj, (dict, Mapping)):
        return {k: _serialize(v) for k, v in obj.items()}
    return obj


def _emit(level: str, msg: str, *, extra: Optional[Mapping[str, Any]] = None) -> None:
    if not _level_enabled(level):
        return
    ts = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())
    record: MutableMapping[str, Any] = {
        "ts": ts,
        "level": level,
        "msg": msg,
    }
    if extra:
        for k, v in extra.items():
            record[k] = _serialize(v)

    out: str
    if _JSON_MODE:
        out = json.dumps(record, ensure_ascii=False, separators=(",", ":"))
    else:
        # Simple key=val formatting
        parts = [f"{k}={json.dumps(v, ensure_ascii=False)}" for k, v in record.items() if k not in {"msg"}]
        out = f"[{record['level']}] {record['msg']} | " + " ".join(parts)
    stream = sys.stderr if level in {"WARN", "ERROR"} else sys.stdout
    print(out, file=stream)


def debug(msg: str, *, extra: Optional[Mapping[str, Any]] = None) -> None:  # noqa: D401
    """Log a DEBUG message."""
    _emit("DEBUG", msg, extra=extra)


def info(msg: str, *, extra: Optional[Mapping[str, Any]] = None) -> None:  # noqa: D401
    """Log an INFO message."""
    _emit("INFO", msg, extra=extra)


def warn(msg: str, *, extra: Optional[Mapping[str, Any]] = None) -> None:  # noqa: D401
    """Log a WARN message."""
    _emit("WARN", msg, extra=extra)


def error(msg: str, *, extra: Optional[Mapping[str, Any]] = None) -> None:  # noqa: D401
    """Log an ERROR message."""
    _emit("ERROR", msg, extra=extra)


__all__ = ["debug", "info", "warn", "error"]
