from __future__ import annotations
"""Local MCP-style HTTP server exposing basic TTS + echo endpoints.

This is a lightweight reproducible HTTP server so ElevenLabs (u otra plataforma)
pueda conectarse como "servidor MCP" personalizado.

Endpoints
---------
GET  /health -> estado y banderas
POST /echo   -> eco de payload JSON
POST /tts    -> sintetiza texto (usa servicio interno si existe, fallback pseudo audio)
GET  /voices -> lista estática de voces (placeholder)
POST /stt    -> (placeholder) decodifica audio base64 y responde transcript ficticio

No introduce dependencias externas (usa stdlib http.server) para mantener
portabilidad. Si en el futuro se requiere streaming, migrar a FastAPI / SSE.
"""
import argparse
import base64
import json
import os
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, Optional, Tuple

try:  # Intento de importar un generador TTS interno si existe
    from backend.src.services.aip_service import tts_generate_bytes  # type: ignore
except Exception:  # pragma: no cover - fallback
    tts_generate_bytes = None  # type: ignore

DEFAULT_HOST = "127.0.0.1"


def _json_response(handler: BaseHTTPRequestHandler, obj: Dict[str, Any], status: int = 200) -> None:
    data = json.dumps(obj, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(data)))
    handler.end_headers()
    handler.wfile.write(data)


class ElevenLabsHandler(BaseHTTPRequestHandler):
    server_version = "CeroDolorMCP/0.1"

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002, D401
        # Silenciar para no llenar la consola (compat firma base class)
        _ = (format, args)

    # Utilidades
    def _read_json(self) -> Tuple[dict[str, Any], Optional[str]]:
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length) if length else b"{}"
        try:
            return json.loads(raw.decode("utf-8") or "{}"), None
        except json.JSONDecodeError as e:  # noqa: F841
            return {}, "invalid_json"

    # Métodos HTTP
    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/health":
            _json_response(self, {
                "status": "ok",
                "ts": time.time(),
                "network": bool(os.getenv("USE_NETWORK")),
                "adapters": bool(os.getenv("USE_ADAPTERS")),
            })
            return
        if self.path == "/voices":
            voices = [
                {"id": "demo_female", "name": "Demo Female", "lang": "es"},
                {"id": "demo_male", "name": "Demo Male", "lang": "es"},
            ]
            _json_response(self, {"voices": voices})
            return
        _json_response(self, {"error": "not_found", "path": self.path}, 404)

    def do_POST(self) -> None:  # noqa: N802
        if self.path == "/echo":
            data, err = self._read_json()
            if err:
                _json_response(self, {"error": err}, 400)
                return
            _json_response(self, {"echo": data, "ts": time.time()})
            return
        if self.path == "/tts":
            data, err = self._read_json()
            if err:
                _json_response(self, {"error": err}, 400)
                return
            text = str(data.get("text") or "").strip()
            voice = str(data.get("voice") or "demo_female")
            if not text:
                _json_response(self, {"error": "text_required"}, 400)
                return
            started = time.time()
            audio_bytes: Optional[bytes] = None
            error: Optional[str] = None
            if tts_generate_bytes:
                try:
                    audio_bytes = tts_generate_bytes(text)
                except Exception as e:  # noqa: BLE001
                    error = f"tts_error:{e}"
            if audio_bytes is None:  # fallback pseudo audio determinista
                pseudo = f"SYNTH::{voice}::{text}".encode("utf-8")
                audio_bytes = pseudo
            b64 = base64.b64encode(audio_bytes).decode("ascii")
            _json_response(self, {
                "voice": voice,
                "text_len": len(text),
                "audio_b64": b64,
                "ms": int((time.time() - started) * 1000),
                "error": error,
            })
            return
        if self.path == "/stt":
            data, err = self._read_json()
            if err:
                _json_response(self, {"error": err}, 400)
                return
            audio_b64 = data.get("audio_b64")
            if not isinstance(audio_b64, str) or not audio_b64:
                _json_response(self, {"error": "audio_b64_required"}, 400)
                return
            # Placeholder: no real decoding/transcripción
            # (Se podría integrar Whisper u otro modelo local más adelante)
            _json_response(self, {
                "transcript": "(placeholder) contenido no transcrito",
                "chars": len(audio_b64),
            })
            return
        _json_response(self, {"error": "not_found", "path": self.path}, 404)


def serve_in_thread(port: int = 0) -> tuple[ThreadingHTTPServer, threading.Thread, int]:
    httpd = ThreadingHTTPServer((DEFAULT_HOST, port), ElevenLabsHandler)
    bound = httpd.server_address[1]
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    return httpd, t, bound


def main() -> None:
    parser = argparse.ArgumentParser(description="CeroDolor ElevenLabs MCP server")
    parser.add_argument("--port", type=int, default=3031)
    args = parser.parse_args()
    httpd, thread, bound = serve_in_thread(args.port)
    print(json.dumps({"status": "listening", "port": bound}))
    try:
        thread.join()
    except KeyboardInterrupt:  # pragma: no cover - manual stop
        httpd.shutdown()


if __name__ == "__main__":  # pragma: no cover
    main()
