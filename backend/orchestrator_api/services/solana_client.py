import asyncio
from typing import Any

from backend.orchestrator_api.config import settings
from backend.orchestrator_api.logging_utils import get_logger

logger = get_logger(__name__)


class SolanaService:
    def __init__(self, rpc_url: str | None = None):
        self.rpc_url = rpc_url or settings.solana_rpc_url

    async def health(self) -> dict[str, Any]:
        if not self.rpc_url:
            return {"ok": False, "reason": "No RPC URL configured"}
        return {"ok": True, "rpc_url": self.rpc_url}

    async def anchor_hash(self, payload_hash_hex: str) -> str:
        await asyncio.sleep(0.05)
        return f"FAKE_SIG_{payload_hash_hex[:16]}"
