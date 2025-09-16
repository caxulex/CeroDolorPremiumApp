from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from json import loads as json_loads
from typing import Any


@dataclass(frozen=True)
class SolanaConfig:
    rpc_url: str | None
    payer_secret: str | None = None


class SolanaClient:
    """Offline-first Solana adapter for micropayments.

    Offline: produces deterministic `signature` based on inputs.
    Real: only when `USE_NETWORK=true` and `SOLANA_RPC_URL`/`SOLANA_PAYER_SECRET` set (not implemented).
    """

    def __init__(self, cfg: SolanaConfig | None = None) -> None:
        rpc_url = os.getenv("SOLANA_RPC_URL")
        payer_secret = os.getenv("SOLANA_PAYER_SECRET")
        self.cfg = cfg or SolanaConfig(rpc_url=rpc_url, payer_secret=payer_secret)
        self._use_network = os.getenv("USE_NETWORK", "false").lower() == "true" and bool(self.cfg.rpc_url and self.cfg.payer_secret)

    def _det_sig(self, *parts: str) -> str:
        src = "|".join(parts)
        return hashlib.sha256(src.encode()).hexdigest()

    def send_micropayment(self, to_address: str, amount_sol: float) -> dict[str, Any]:
        if not self._use_network:
            return {"signature": f"SIM_SIG_{self._det_sig(to_address, str(amount_sol))[:16]}", "amount_sol": amount_sol}
        # Minimal placeholder network call: getLatestBlockhash to prove RPC
        try:
            import requests

            url = (self.cfg.rpc_url or "").rstrip("/")
            if not url:
                return {"error": "missing_rpc_url"}
            payload = {"jsonrpc": "2.0", "id": 1, "method": "getLatestBlockhash"}
            resp = requests.post(url, json=payload, timeout=10)
            if resp.status_code >= 400:  # noqa: PLR2004
                return {"error": "http_error", "status": resp.status_code, "text": resp.text[:500]}
            data = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else json_loads(resp.text)
            blockhash = (
                data.get("result", {})
                .get("value", {})
                .get("blockhash")
            )
            # We are not actually signing/sending a tx here; return a structured placeholder
            return {"latest_blockhash": blockhash, "amount_sol": amount_sol}  # noqa: TRY300
        except Exception as e:  # noqa: BLE001
            return {"error": "exception", "message": str(e)[:500]}

    def get_latest_blockhash(self) -> dict[str, Any]:
        """Fetch latest blockhash via RPC when network is enabled.

        Returns offline deterministic data otherwise.
        """
        if not self._use_network:
            return {"latest_blockhash": self._det_sig("offline", "bh")[:32]}
        try:
            import requests

            url = (self.cfg.rpc_url or "").rstrip("/")
            if not url:
                return {"error": "missing_rpc_url"}
            payload = {"jsonrpc": "2.0", "id": 1, "method": "getLatestBlockhash"}
            resp = requests.post(url, json=payload, timeout=10)
            if resp.status_code >= 400:  # noqa: PLR2004
                return {"error": "http_error", "status": resp.status_code, "text": resp.text[:500]}
            data = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else json_loads(resp.text)
            blockhash = (
                data.get("result", {})
                .get("value", {})
                .get("blockhash")
            )
            return {"latest_blockhash": blockhash}  # noqa: TRY300
        except Exception as e:  # noqa: BLE001
            return {"error": "exception", "message": str(e)[:500]}
