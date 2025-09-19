import json

import pytest

from backend.src.utils.encryption import decrypt_json, encrypt_json


@pytest.mark.skipif('cryptography' not in __import__('sys').modules and False, reason="Needs cryptography if installed")
def test_encrypt_decrypt_roundtrip():
    sample = json.dumps({"a": 1, "b": "x"})
    password = "secret123"
    enc = encrypt_json(sample, password)
    out = decrypt_json(enc, password)
    assert out == sample
