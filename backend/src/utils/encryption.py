"""Optional Fernet encryption helper for session export.

We only import `cryptography` lazily so the project runs even if dependency
is absent. Functions fall back gracefully.

Public API:
- derive_key(password: str, *, salt: bytes | None = None) -> tuple[key: bytes, salt: bytes]
- encrypt_json(text: str, password: str) -> str  (returns base64 token or raises)
- decrypt_json(token: str, password: str, salt_b64: str) -> str

Format of returned encrypted export (JSON string):
{
  "enc": "fernet",
  "salt": <base64>,
  "token": <fernet token base64>
}
If cryptography is missing: raises RuntimeError("encryption_unavailable").
"""
from __future__ import annotations

import base64
import json
import os
from hashlib import sha256
from typing import Tuple


def _require_crypto():
    try:
        from cryptography.fernet import Fernet  # type: ignore
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC  # type: ignore
        from cryptography.hazmat.primitives import hashes  # type: ignore
        from cryptography.hazmat.backends import default_backend  # type: ignore
    except Exception as e:  # noqa: BLE001
        raise RuntimeError("encryption_unavailable") from e
    return Fernet, PBKDF2HMAC, hashes, default_backend


def derive_key(password: str, *, salt: bytes | None = None) -> Tuple[bytes, bytes]:
    if not isinstance(password, str) or not password:
        raise ValueError("password_required")
    Fernet, PBKDF2HMAC, hashes, default_backend = _require_crypto()
    salt = salt or os.urandom(16)
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=390000,
        backend=default_backend(),
    )
    key = base64.urlsafe_b64encode(kdf.derive(password.encode("utf-8")))
    return key, salt


def encrypt_json(text: str, password: str) -> str:
    key, salt = derive_key(password)
    Fernet, *_ = _require_crypto()
    f = Fernet(key)
    token = f.encrypt(text.encode("utf-8"))
    payload = {
        "enc": "fernet",
        "salt": base64.b64encode(salt).decode("ascii"),
        "token": token.decode("ascii"),
    }
    return json.dumps(payload, ensure_ascii=False)


def decrypt_json(token_payload: str, password: str) -> str:
    data = json.loads(token_payload)
    if data.get("enc") != "fernet":
        raise ValueError("unsupported_format")
    salt_b64 = data.get("salt")
    token = data.get("token")
    if not isinstance(salt_b64, str) or not isinstance(token, str):
        raise ValueError("invalid_payload")
    salt = base64.b64decode(salt_b64)
    key, _ = derive_key(password, salt=salt)
    Fernet, *_ = _require_crypto()
    f = Fernet(key)
    out = f.decrypt(token.encode("ascii"))
    return out.decode("utf-8")


__all__ = ["encrypt_json", "decrypt_json", "derive_key"]
