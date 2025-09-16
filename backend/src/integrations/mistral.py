from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class MistralConfig:
    api_key: str | None
    model: str = "mistral-large-latest"
    base_url: str | None = None


class MistralClient:
    """Env-guarded minimal LLM client with offline simulation.

    Only calls network if MISTRAL_API_KEY is set and USE_NETWORK=true.
    """

    def __init__(self, cfg: MistralConfig | None = None) -> None:
        api_key = os.getenv("MISTRAL_API_KEY")
        use_network = os.getenv("USE_NETWORK", "false").lower() == "true"
        base_url = os.getenv("MISTRAL_BASE_URL")
        self.cfg = cfg or MistralConfig(api_key=api_key, base_url=base_url)
        self._use_network = use_network and bool(self.cfg.api_key)

    def chat(self, _messages: list[dict[str, str]], *, _system: str | None = None) -> dict[str, Any]:
        """Chat completion.

        Behavior:
        - Offline simulation (default): returns a deterministic assistant message for tests.
        - Real API call: only attempted when both `MISTRAL_API_KEY` is set and `USE_NETWORK=true`.
        """
        if not self._use_network:
            # Simulated reasoning output for tests
            content = "simulado: plan de intervención basado en señales clínicas"
            return {"id": "sim-chat", "choices": [{"message": {"role": "assistant", "content": content}}]}
        # Placeholder for real API call
        return {"error": "network_not_implemented"}

    def extract(self, _text: str, *, _schema: dict[str, Any] | None = None) -> dict[str, Any]:
        """Simple structured extraction.

        Behavior:
        - Offline simulation (default): returns a fixed structure. Optionally consider `_schema` in future.
        - Real API call: only attempted when both `MISTRAL_API_KEY` is set and `USE_NETWORK=true`.
        """
        if not self._use_network:
            # Simulated structured extraction
            return {"pain_location": "espalda baja", "intensity": 5, "triggers": ["mañanas"]}
        return {"error": "network_not_implemented"}
