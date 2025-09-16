"""Centralized logging configuration for backend components.

Provides a `get_logger` helper that returns a module-scoped logger
with structured, minimal formatting. Respects LOG_LEVEL env var.
Does not alter existing code paths; importing is optional.
"""

from __future__ import annotations

import logging
import os

_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
_CONFIGURED = False


def _configure_root() -> None:
    global _CONFIGURED  # noqa: PLW0603
    if _CONFIGURED:
        return
    level = getattr(logging, _LEVEL, logging.INFO)
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%H:%M:%S",
    )
    handler.setFormatter(formatter)
    root = logging.getLogger()
    root.setLevel(level)
    # Avoid duplicate handlers if re-imported
    if not root.handlers:
        root.addHandler(handler)
    _CONFIGURED = True


def get_logger(name: str | None = None) -> logging.Logger:
    """Return a logger configured once.

    Parameters
    ----------
    name: Optional module or logical component name.
    """
    _configure_root()
    return logging.getLogger(name)


def set_level(level: str) -> None:
    """Dynamically adjust root log level (for tests or REPL)."""
    _configure_root()
    logging.getLogger().setLevel(getattr(logging, level.upper(), logging.INFO))


__all__ = ["get_logger", "set_level"]
