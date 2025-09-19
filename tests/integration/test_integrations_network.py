import os

import pytest

require_network = pytest.mark.skipif(
    os.getenv("USE_NETWORK", "false").lower() != "true",
    reason="USE_NETWORK!=true; skipping network tests",
)


@require_network
def test_crossmint_network_paths():
    from backend.src.integrations.crossmint import CrossmintClient, CrossmintConfig

    if not os.getenv("CROSSMINT_API_KEY"):
        pytest.skip("No CROSSMINT_API_KEY set")
    base_url = os.getenv("CROSSMINT_BASE_URL")
    client = CrossmintClient(CrossmintConfig(api_key=os.getenv("CROSSMINT_API_KEY"), base_url=base_url))

    # create wallet
    res = client.create_wallet("test-user")
    assert isinstance(res, dict)
    assert "address" in res or "error" in res

    # mint nft
    res2 = client.mint_nft(res.get("address", "CM_DEMO_ADDR"), {"name": "Demo", "desc": "Test"})
    assert isinstance(res2, dict)
    assert "token_id" in res2 or "error" in res2

    # transfer nft (to self demo)
    if "token_id" in res2:
        res3 = client.transfer_nft(res2["token_id"], res.get("address", "CM_DEMO_ADDR"))
        assert isinstance(res3, dict)
        assert "transfer_tx" in res3 or "error" in res3


@require_network
def test_solana_network_paths():
    from backend.src.integrations.solana import SolanaClient, SolanaConfig

    if not os.getenv("SOLANA_RPC_URL"):
        pytest.skip("No SOLANA_RPC_URL set")
    client = SolanaClient(SolanaConfig(rpc_url=os.getenv("SOLANA_RPC_URL"), payer_secret=os.getenv("SOLANA_PAYER_SECRET")))

    bh = client.get_latest_blockhash()
    assert isinstance(bh, dict)
    assert "latest_blockhash" in bh or "error" in bh

    res = client.send_micropayment("DEMO_TO_ADDRESS", 0.000001)
    assert isinstance(res, dict)
    assert any(k in res for k in ("latest_blockhash", "signature", "error"))
