"""Anonymization strategies (deterministic offline).

Currently provides a hash surrogate method and field filtering.
"""
from __future__ import annotations

import hashlib
import json
from typing import Iterable, Dict, Any


def hash_surrogate(obj: Any) -> str:
    data = json.dumps(obj, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def filter_fields(data: Dict[str, Any], fields: Iterable[str]) -> Dict[str, Any]:
    return {k: data.get(k) for k in fields}


def anonymize_payload(data: Dict[str, Any], fields: Iterable[str]) -> dict[str, Any]:
    subset = filter_fields(data, fields)
    return {"hash": hash_surrogate(subset), "fields": list(fields)}


__all__ = [
    "hash_surrogate",
    "filter_fields",
    "anonymize_payload",
]
