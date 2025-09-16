from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class CrossmintConfig:
    api_key: str | None
    base_url: str | None = None
    collection_id: str | None = None


class CrossmintClient:
    """Offline-first Crossmint adapter.

    Behavior:
    - Offline simulation (default): deterministic wallet IDs, NFT token IDs, and tx IDs.
    - Real API calls: only when `USE_NETWORK=true` and `CROSSMINT_API_KEY` is set.
    """

    def __init__(self, cfg: CrossmintConfig | None = None) -> None:
        api_key = os.getenv("CROSSMINT_API_KEY")
        base_url = os.getenv("CROSSMINT_BASE_URL")
        collection_id = os.getenv("CROSSMINT_COLLECTION_ID")
        self.cfg = cfg or CrossmintConfig(api_key=api_key, base_url=base_url, collection_id=collection_id)
        self._use_network = os.getenv("USE_NETWORK", "false").lower() == "true" and bool(self.cfg.api_key)

    def _det_hash(self, s: str, length: int = 10) -> str:
        return hashlib.sha256(s.encode()).hexdigest()[:length]

    def create_wallet(self, user_id: str) -> dict[str, Any]:
        """Provision a wallet for a given user id.

        Offline: returns deterministic `address` derived from `user_id`.
        """
        if not self._use_network:
            return {"address": f"CM{self._det_hash('w:'+user_id, 16)}"}
        return {"error": "network_not_implemented"}

    def mint_nft(self, owner_address: str, metadata: dict[str, Any]) -> dict[str, Any]:
        """Mint an NFT representing a data asset to `owner_address`.

        Offline: returns deterministic `token_id` and a fake tx id.
        """
        _ = metadata
        if not self._use_network:
            token_id = f"NFT{self._det_hash('t:'+owner_address, 8)}"
            return {"token_id": token_id, "mint_tx": f"CM_TX_{self._det_hash(token_id, 12)}"}
        return {"error": "network_not_implemented"}

    def transfer_nft(self, token_id: str, to_address: str) -> dict[str, Any]:
        """Transfer NFT to `to_address`.

        Offline: returns fake `transfer_tx` id.
        """
        if not self._use_network:
            return {"transfer_tx": f"CM_TX_{self._det_hash(token_id+to_address, 12)}"}
        return {"error": "network_not_implemented"}
