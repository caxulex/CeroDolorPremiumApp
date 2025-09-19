import base64

import httpx

from backend.orchestrator_api.config import settings
from backend.orchestrator_api.logging_utils import get_logger

logger = get_logger(__name__)


class ElevenLabsClient:
    def __init__(self, api_key: str | None = None, base_url: str | None = None):
        self.api_key = api_key or settings.elevenlabs_api_key
        self.base_url = base_url or str(settings.elevenlabs_base_url)
        self._client = httpx.AsyncClient(base_url=self.base_url, timeout=30)

    async def close(self) -> None:
        await self._client.aclose()

    def _headers(self) -> dict:
        return {"xi-api-key": self.api_key} if self.api_key else {}

    async def synthesize(self, text: str, *, voice_id: str | None = None) -> str | None:
        if not settings.use_network or not self.api_key:
            return None
        v = voice_id or settings.elevenlabs_default_voice
        path = f"/v1/text-to-speech/{v}/stream"
        try:
            r = await self._client.post(path, headers=self._headers(), json={"text": text})
            r.raise_for_status()
            return base64.b64encode(r.content).decode("ascii")
        except Exception:
            logger.exception("ElevenLabs synth failed")
            return None
