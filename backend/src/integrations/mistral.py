from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Dict, List
import json
import requests


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

    def chat(self, _messages: list[dict[str, str]], *, _system: str | None = None, timeout_s: int | None = 60) -> dict[str, Any]:
        """Chat completion.

        Behavior:
        - Offline simulation (default): returns a deterministic assistant message for tests.
        - Real API call: only attempted when both `MISTRAL_API_KEY` is set and `USE_NETWORK=true`.
        """
        if not self._use_network:
            content = "simulado: plan de intervención basado en señales clínicas"
            return {"id": "sim-chat", "choices": [{"message": {"role": "assistant", "content": content}}]}
        try:
            base = self.cfg.base_url or "https://api.mistral.ai"
            url = f"{base.rstrip('/')}/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.cfg.api_key}",
                "Content-Type": "application/json",
            }
            payload: Dict[str, Any] = {
                "model": self.cfg.model,
                "messages": _messages,
            }
            if _system:
                payload["system"] = _system
            resp = requests.post(url, headers=headers, data=json.dumps(payload), timeout=timeout_s or 60)
            if resp.status_code >= 400:
                return {"error": "http_error", "status": resp.status_code, "text": resp.text[:400]}
            return resp.json()
        except Exception as e:  # noqa: BLE001
            return {"error": "exception", "reason": str(e)}

    def extract(self, _text: str, *, _schema: dict[str, Any] | None = None) -> dict[str, Any]:
        """Simple structured extraction.

        Behavior:
        - Offline simulation (default): returns a fixed structure. Optionally consider `_schema` in future.
        - Real API call: only attempted when both `MISTRAL_API_KEY` is set and `USE_NETWORK=true`.
        """
        if not self._use_network:
            return {"pain_location": "espalda baja", "intensity": 5, "triggers": ["mañanas"]}
        # For extraction, emulate a structured prompt via chat endpoint
        try:
            chat_res = self.chat([
                {"role": "user", "content": f"Extrae estructura JSON del texto: {_text}"},
            ])
            if "error" in chat_res:
                return chat_res
            # Heuristic parse: look for JSON block in content
            choices = chat_res.get("choices") if isinstance(chat_res, dict) else None
            if choices:
                content = choices[0].get("message", {}).get("content", "")  # type: ignore[index]
                # Extremely simple heuristic; in real use implement robust parsing
                if content.strip().startswith("{") and content.strip().endswith("}"):
                    try:
                        return json.loads(content)
                    except Exception:  # noqa: BLE001
                        pass
            return {"raw": chat_res}
        except Exception as e:  # noqa: BLE001
            return {"error": "exception", "reason": str(e)}
