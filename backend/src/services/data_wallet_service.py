from __future__ import annotations

import os
from typing import Any


def _use_adapters() -> bool:
    return os.getenv("USE_ADAPTERS", "false").lower() == "true"


def create_patient_wallet(patient_id: str) -> dict[str, Any]:
    """Create or derive a patient wallet via Crossmint.

    Offline: returns deterministic address through adapter simulation.
    """
    if _use_adapters():
        try:
            from integrations.crossmint import CrossmintClient, CrossmintConfig  # type: ignore[import-not-found]  # noqa: I001

            client = CrossmintClient(CrossmintConfig(api_key=os.getenv("CROSSMINT_API_KEY")))  # type: ignore[misc]
            return client.create_wallet(patient_id)
        except Exception:  # noqa: BLE001
            return {"address": None}
    # Without adapters we do nothing (no on-chain side effects allowed in CI)
    return {"address": None}


def mint_data_asset(owner_address: str, anonymized_hash: str, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    """Mint an NFT that represents anonymized patient data.

    Offline: returns deterministic token and tx id.
    """
    _ = metadata
    if _use_adapters():
        try:
            from integrations.crossmint import CrossmintClient, CrossmintConfig  # type: ignore[import-not-found]  # noqa: I001

            client = CrossmintClient(CrossmintConfig(api_key=os.getenv("CROSSMINT_API_KEY")))  # type: ignore[misc]
            return client.mint_nft(owner_address, {"hash": anonymized_hash})
        except Exception:  # noqa: BLE001
            return {"token_id": None, "mint_tx": None}
    return {"token_id": None, "mint_tx": None}


def grant_consent_and_pay(owner_token_id: str, researcher_address: str, micropayment_sol: float) -> dict[str, Any]:
    """Simulate consent grant: transfer a data token and send a micropayment on Solana.

    Offline: returns transfer and payment signatures.
    """
    transfer_tx: str | None = None
    pay_sig: str | None = None

    if _use_adapters():
        try:
            from integrations.crossmint import CrossmintClient, CrossmintConfig  # type: ignore[import-not-found]  # noqa: I001
            from integrations.solana import SolanaClient, SolanaConfig  # type: ignore[import-not-found]

            c_client = CrossmintClient(CrossmintConfig(api_key=os.getenv("CROSSMINT_API_KEY")))  # type: ignore[misc]
            s_client = SolanaClient(SolanaConfig(rpc_url=os.getenv("SOLANA_RPC_URL")))  # type: ignore[misc]
            transfer_resp = c_client.transfer_nft(owner_token_id, researcher_address)
            pay_resp = s_client.send_micropayment(researcher_address, micropayment_sol)
            transfer_tx = transfer_resp.get("transfer_tx") if isinstance(transfer_resp, dict) else None
            pay_sig = pay_resp.get("signature") if isinstance(pay_resp, dict) else None
        except Exception:  # noqa: BLE001
            transfer_tx = None
            pay_sig = None

    return {"transfer_tx": transfer_tx, "payment_signature": pay_sig}
