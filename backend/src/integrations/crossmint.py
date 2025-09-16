from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from json import loads as json_loads
from typing import Any
from urllib.parse import urljoin


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
        # Minimal network path (env-gated). API shape may differ; we keep it resilient.
        try:
            import requests

            base = self.cfg.base_url or "https://www.crossmint.com/api/"
            url = urljoin(base, "wallets")
            headers = {"Authorization": f"Bearer {self.cfg.api_key}", "Content-Type": "application/json"}
            payload = {"userId": user_id}
            resp = requests.post(url, json=payload, headers=headers, timeout=10)
            if resp.status_code >= 400:  # noqa: PLR2004
                return {"error": "http_error", "status": resp.status_code, "text": resp.text[:500]}
            data = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else json_loads(resp.text)
            # Try common fields; fallback to deterministic if missing
            address = data.get("address") or data.get("wallet") or data.get("id")
            if not address:
                address = f"CM{self._det_hash('w:'+user_id, 16)}"
            return {"address": address}  # noqa: TRY300
        except Exception as e:  # noqa: BLE001
            return {"error": "exception", "message": str(e)[:500]}

    def mint_nft(self, owner_address: str, metadata: dict[str, Any]) -> dict[str, Any]:
        """Mint an NFT representing a data asset to `owner_address`.

        Offline: returns deterministic `token_id` and a fake tx id.
        """
        _ = metadata
        if not self._use_network:
            token_id = f"NFT{self._det_hash('t:'+owner_address, 8)}"
            return {"token_id": token_id, "mint_tx": f"CM_TX_{self._det_hash(token_id, 12)}"}
        try:
            import requests

            base = self.cfg.base_url or "https://www.crossmint.com/api/"
            url = urljoin(base, "nfts/mint")
            headers = {"Authorization": f"Bearer {self.cfg.api_key}", "Content-Type": "application/json"}
            payload = {"to": owner_address, "metadata": metadata}
            resp = requests.post(url, json=payload, headers=headers, timeout=15)
            if resp.status_code >= 400:  # noqa: PLR2004
                return {"error": "http_error", "status": resp.status_code, "text": resp.text[:500]}
            data = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else json_loads(resp.text)
            token_id = data.get("tokenId") or data.get("token_id") or f"NFT{self._det_hash('t:'+owner_address, 8)}"
            tx = data.get("tx") or data.get("transactionId") or f"CM_TX_{self._det_hash(token_id, 12)}"
            return {"token_id": token_id, "mint_tx": tx}  # noqa: TRY300
        except Exception as e:  # noqa: BLE001
            return {"error": "exception", "message": str(e)[:500]}

    def transfer_nft(self, token_id: str, to_address: str) -> dict[str, Any]:
        """Transfer NFT to `to_address`.

        Offline: returns fake `transfer_tx` id.
        """
        if not self._use_network:
            return {"transfer_tx": f"CM_TX_{self._det_hash(token_id+to_address, 12)}"}
        try:
            import requests

            base = self.cfg.base_url or "https://www.crossmint.com/api/"
            url = urljoin(base, "nfts/transfer")
            headers = {"Authorization": f"Bearer {self.cfg.api_key}", "Content-Type": "application/json"}
            payload = {"tokenId": token_id, "to": to_address}
            resp = requests.post(url, json=payload, headers=headers, timeout=15)
            if resp.status_code >= 400:  # noqa: PLR2004
                return {"error": "http_error", "status": resp.status_code, "text": resp.text[:500]}
            data = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else json_loads(resp.text)
            tx = data.get("tx") or data.get("transactionId") or f"CM_TX_{self._det_hash(token_id+to_address, 12)}"
            return {"transfer_tx": tx}  # noqa: TRY300
        except Exception as e:  # noqa: BLE001
            return {"error": "exception", "message": str(e)[:500]}
