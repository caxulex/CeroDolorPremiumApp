from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
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
        return {"error": "network_not_implemented"}
