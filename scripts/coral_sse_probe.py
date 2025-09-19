#!/usr/bin/env python3
"""
Minimal probe to check which HTTP paths respond on Coral's port 5555.
It tries a small set of candidate SSE endpoints and prints status and headers.
Uses only the Python standard library (no extra deps).
"""
from __future__ import annotations

import http.client
from urllib.parse import urlparse

CANDIDATE_PATHS = [
    "/",
    "/sse",
    "/mcp/sse",
    "/events",
    "/api/sse",
]

DEFAULT_URL = "http://localhost:5555"

def check_path(base_url: str, path: str) -> None:
    parsed = urlparse(base_url)
    host = parsed.hostname or "localhost"
    port = parsed.port or (443 if parsed.scheme == "https" else 80)

    conn_cls = http.client.HTTPSConnection if parsed.scheme == "https" else http.client.HTTPConnection
    conn = conn_cls(host, port, timeout=10)
    try:
        conn.request("GET", path, headers={"Accept": "text/event-stream"})
        resp = conn.getresponse()
        print(f"GET {path} -> {resp.status} {resp.reason}")
        # Print a few headers to see if it's event-stream
        ct = resp.getheader("Content-Type")
        if ct:
            print(f"  Content-Type: {ct}")
        cache = resp.getheader("Cache-Control")
        if cache:
            print(f"  Cache-Control: {cache}")
    except Exception as e:
        print(f"GET {path} -> ERROR: {e}")
    finally:
        try:
            conn.close()
        except Exception:
            pass

if __name__ == "__main__":
    base = DEFAULT_URL
    print(f"Probing Coral at {base} ...")
    for p in CANDIDATE_PATHS:
        check_path(base, p)
