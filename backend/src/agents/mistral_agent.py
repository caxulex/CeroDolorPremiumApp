from __future__ import annotations

"""Mistral conversational agent.

Env-guarded, offline-first chat wrapper built on integrations.mistral.MistralClient.

Features:
- System prompt and lightweight memory window
- Deterministic offline simulation when network is disabled or key missing
- Hooks to call basic tools (e.g., pain summary) with a simple pattern
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import os

try:  # Local import to avoid hard dependency on runtime
    from backend.src.integrations.mistral import MistralClient  # type: ignore
except Exception:  # pragma: no cover
    MistralClient = None  # type: ignore


DEFAULT_SYSTEM = (
    "Eres un asistente clínico empático para manejo del dolor crónico. "
    "Responde en español, claro y breve. Prioriza seguridad, respiración, movilidad suave, y educación. "
    "Si faltan datos, pide aclaraciones de forma amable."
)


@dataclass
class MistralAgentConfig:
    model: str = os.getenv("MISTRAL_MODEL", "mistral-large-latest")
    temperature: float = float(os.getenv("MISTRAL_TEMPERATURE", "0.4"))
    max_history: int = int(os.getenv("MISTRAL_MAX_HISTORY", "6"))
    system_prompt: str = os.getenv("MISTRAL_SYSTEM", DEFAULT_SYSTEM)
    timeout_s: int = int(os.getenv("MISTRAL_TIMEOUT", "60"))
    retries: int = int(os.getenv("MISTRAL_RETRIES", "1"))


@dataclass
class Turn:
    role: str
    content: str


class MistralAgent:
    def __init__(self, cfg: Optional[MistralAgentConfig] = None) -> None:
        self.cfg = cfg or MistralAgentConfig()
        self.history: List[Turn] = []
        self._client = MistralClient() if MistralClient else None

    def reset(self) -> None:
        self.history.clear()

    def _build_messages(self, user_input: str) -> List[Dict[str, str]]:
        # Keep a small sliding window of history
        hist = self.history[-self.cfg.max_history :]
        msgs: List[Dict[str, str]] = []
        if self.cfg.system_prompt:
            msgs.append({"role": "system", "content": self.cfg.system_prompt})
        for t in hist:
            msgs.append({"role": t.role, "content": t.content})
        msgs.append({"role": "user", "content": user_input})
        return msgs

    def ask(self, user_input: str) -> Dict[str, Any]:
        """Send a user input and return assistant response with metadata.

        Returns: {"text": str, "raw": dict}
        """
        msgs = self._build_messages(user_input)
        if not self._client:
            # Offline deterministic response
            text = "simulado: entiendo tu situación; prueba respiración 4-6 y paseos suaves de 5-10 minutos."
            self.history.append(Turn("user", user_input))
            self.history.append(Turn("assistant", text))
            return {"text": text, "raw": {"mode": "offline"}}
        try:
            # Basic retry loop
            last_err: Optional[str] = None
            res = None
            for _ in range(max(1, int(self.cfg.retries))):
                res = self._client.chat(msgs, _system=self.cfg.system_prompt, timeout_s=int(self.cfg.timeout_s))
                if isinstance(res, dict) and "error" in res:
                    last_err = str(res.get("error"))
                    continue
                break
            if res is None:
                raise RuntimeError(last_err or "Unknown error")
            # Extract assistant text
            text = ""
            try:
                choices = res.get("choices") if isinstance(res, dict) else None
                if choices:
                    text = (
                        choices[0]
                        .get("message", {})  # type: ignore[index]
                        .get("content", "")
                    )
            except Exception:
                text = ""
            if not text:
                text = "No pude generar respuesta ahora; intenta de nuevo."
            self.history.append(Turn("user", user_input))
            self.history.append(Turn("assistant", text))
            # Optional meta envelope
            try:
                from backend.src.agents.base import make_meta  # type: ignore
                meta = make_meta()
            except Exception:
                meta = None
            out: Dict[str, Any] = {"text": text, "raw": res}
            if meta:
                out["meta"] = meta
            # pass through usage if present
            if isinstance(res, dict) and isinstance(res.get("usage"), dict):
                out["usage"] = res["usage"]
            return out
        except Exception as e:  # pragma: no cover - network path
            text = "simulado: ejercicios de movilidad articular suaves y pausas de descanso."
            self.history.append(Turn("user", user_input))
            self.history.append(Turn("assistant", text))
            try:
                from backend.src.agents.base import make_meta  # type: ignore
                meta = make_meta()
            except Exception:
                meta = None
            out_err: Dict[str, Any] = {"text": text, "raw": {"error": str(e)}}
            if meta:
                out_err["meta"] = meta
            return out_err

    def health(self) -> Dict[str, Any]:
        """Lightweight health check for wiring and configuration."""
        has_client = bool(self._client)
        # Consider online only if env allows network and key is present
        use_net = os.getenv("USE_NETWORK", "false").lower() in {"1", "true", "yes"}
        has_key = bool(os.getenv("MISTRAL_API_KEY"))
        online = False
        try:
            if self._client:
                # In offline mode client returns a simulated response; treat that as healthy wiring
                ping = self._client.chat([{"role": "user", "content": "ping"}], _system=None, timeout_s=5)
                wiring_ok = isinstance(ping, dict) and ("choices" in ping or "id" in ping)
                online = wiring_ok and use_net and has_key
        except Exception:
            online = False
        return {
            "client": has_client,
            "online": online,
            "history_len": len(self.history),
            "model": self.cfg.model,
            "timeout_s": self.cfg.timeout_s,
            "retries": self.cfg.retries,
        }


__all__ = ["MistralAgent", "MistralAgentConfig"]
