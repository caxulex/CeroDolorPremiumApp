import asyncio
from typing import Any

import httpx

from backend.orchestrator_api.config import settings
from backend.orchestrator_api.logging_utils import get_logger

logger = get_logger(__name__)


class MistralError(Exception):
    pass


class MistralClient:
    def __init__(self, api_key: str | None = None, base_url: str | None = None):
        self.api_key = api_key or settings.mistral_api_key
        self.base_url = base_url or str(settings.mistral_base_url)
        self._client = httpx.AsyncClient(base_url=self.base_url, timeout=30)

    async def close(self) -> None:
        await self._client.aclose()

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}

    MAX_OK_STATUS = 499

    async def health(self) -> dict[str, Any]:
        try:
            r = await self._client.get(settings.mistral_health_path, headers=self._headers())
        except httpx.HTTPError as e:  # pragma: no cover - simple pass-through
            return {"ok": False, "error": str(e)}
        else:
            return {"ok": r.status_code <= self.MAX_OK_STATUS, "status": r.status_code}

    async def invoke_agent(self, agent_id: str, payload: dict[str, Any], *, retries: int = 2) -> dict[str, Any]:
        path = settings.mistral_agent_invoke_path.format(agent_id=agent_id)
        last_exc: Exception | None = None
        for attempt in range(retries + 1):
            try:
                r = await self._client.post(path, json=payload, headers=self._headers())
                if r.status_code in (429,) or r.status_code > self.MAX_OK_STATUS:
                    msg = f"Mistral error: {r.status_code}"
                    raise MistralError(msg)
                r.raise_for_status()
                return r.json() if r.content else {}
            except httpx.HTTPError as e:
                last_exc = e
                wait = min(2 ** attempt, 4)
                logger.warning("invoke_agent retry attempt=%s wait=%ss error=%s", attempt, wait, e)
                await asyncio.sleep(wait)
        raise MistralError(str(last_exc) if last_exc else "Unknown Mistral error")
