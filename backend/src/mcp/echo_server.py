from __future__ import annotations

import argparse
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any


class EchoHandler(BaseHTTPRequestHandler):
    server_version = "EchoHTTP/0.1"

    def _set_headers(self, status: int = 200, content_type: str = "application/json") -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.end_headers()

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
        # Quiet handler for tests/demo: mark args as used to satisfy linters
        _ = (format, args)

    def do_GET(self) -> None:  # noqa: N802
        if self.path.startswith("/health"):
            self._set_headers(200)
            self.wfile.write(json.dumps({"status": "ok"}).encode())
        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({"error": "NotFound"}).encode())

    def do_POST(self) -> None:  # noqa: N802
        if self.path.startswith("/echo"):
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length) if length else b""
            try:
                data = json.loads(body.decode() or "{}")
                self._set_headers(200)
                self.wfile.write(json.dumps({"ok": True, "received": data}).encode())
            except json.JSONDecodeError:
                self._set_headers(200)
                self.wfile.write(json.dumps({"ok": True, "text": body.decode(errors="ignore")}).encode())
        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({"error": "NotFound"}).encode())


def serve_in_thread(port: int = 0) -> tuple[ThreadingHTTPServer, threading.Thread, int]:
    """Start echo server in a background thread.

    Returns (server, thread, bound_port).
    """
    httpd = ThreadingHTTPServer(("", port), EchoHandler)
    bound_port = httpd.server_address[1]
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    return httpd, t, bound_port


def run_server(port: int = 3000) -> None:
    httpd = ThreadingHTTPServer(("", port), EchoHandler)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:  # pragma: no cover - manual stop
        pass
    finally:
        httpd.server_close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Simple local MCP echo server")
    parser.add_argument("--port", type=int, default=3000)
    args = parser.parse_args()
    run_server(args.port)
