from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class AIMLConfig:
    api_key: str | None
    base_url: str | None


class AIMLClient:
    """Generic AI/ML gateway client with offline simulation for niche tasks (sentiment, posture hints)."""

    def __init__(self, cfg: AIMLConfig | None = None) -> None:
        api_key = os.getenv("AIML_API_KEY")
        use_network = os.getenv("USE_NETWORK", "false").lower() == "true"
        base_url = os.getenv("AIML_BASE_URL")
        self.cfg = cfg or AIMLConfig(api_key=api_key, base_url=base_url)
        self._use_network = use_network and bool(self.cfg.api_key)

    def sentiment(self, _text: str, *, _language: str | None = None) -> dict[str, Any]:
        """Naive sentiment analysis.

        Behavior:
        - Offline simulation (default): returns a simple label based on keywords.
        - Real API call: only attempted if `AIML_API_KEY` is set and `USE_NETWORK=true` (not implemented yet).
        """
        if not self._use_network:
            # Very naive simulated sentiment
            t = _text.lower()
            label = "positivo" if "bien" in t else ("negativo" if "dolor" in t else "neutral")
            return {"label": label, "confidence": 0.8, "language": _language or "es"}
        return {"error": "network_not_implemented"}

    def posture_hint(self, _image_bytes: bytes) -> dict[str, Any]:
        """Return a naive posture hint.

        Behavior:
        - Offline simulation (default): returns a fixed finding.
        - Real API call: only attempted if `AIML_API_KEY` is set and `USE_NETWORK=true` (not implemented yet).
        """
        if not self._use_network:
            return {"finding": "posible cifosis leve", "confidence": 0.65}
        return {"error": "network_not_implemented"}
