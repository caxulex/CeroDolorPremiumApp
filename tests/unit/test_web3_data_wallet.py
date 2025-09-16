from __future__ import annotations

import os

from backend.src.services import data_wallet_service as dws


def setup_module(module):  # noqa: D401 - pytest-style
    os.environ["USE_ADAPTERS"] = "true"
    os.environ["USE_NETWORK"] = "false"
    os.environ.pop("CROSSMINT_API_KEY", None)
    os.environ.pop("SOLANA_RPC_URL", None)


def test_create_patient_wallet_offline():
    res = dws.create_patient_wallet("patient-123")
    assert isinstance(res, dict)
    # address can be None offline if adapters unavailable; with adapters it is deterministic
    assert "address" in res


def test_mint_data_asset_offline():
    wallet = dws.create_patient_wallet("patient-abc")
    addr = wallet.get("address")
    res = dws.mint_data_asset(addr or "addr-none", anonymized_hash="hash123")
    assert isinstance(res, dict)
    assert "token_id" in res


def test_consent_and_micropayment_offline():
    wallet = dws.create_patient_wallet("patient-xyz")
    addr = wallet.get("address") or "addr-none"
    mint = dws.mint_data_asset(addr, anonymized_hash="hash456")
    token_id = mint.get("token_id") or "token-none"
    res = dws.grant_consent_and_pay(token_id, researcher_address="researcher-1", micropayment_sol=0.001)
    assert isinstance(res, dict)
    assert "transfer_tx" in res and "payment_signature" in res
