"""Streamlit UI for CeroDolor (Producto simplificado).

Se enfoca en tres pestañas:
1. Chequeo Diario: Registro y ciclo voz/texto + sugerencia.
2. Progreso: Tendencias y adherencia básica.
3. Avanzado: Diagnóstico técnico y exportación.
"""

from __future__ import annotations

import json
import secrets
import subprocess
import sys
from datetime import datetime
import io
import wave
import time
import base64
import re
from pathlib import Path
from statistics import mean
from typing import Any, Dict, List

import streamlit as st
from streamlit.components.v1 import html as _html  # lightweight HTML injector for lang and minor hooks
import os
try:  # optional dependency for live audio
    from streamlit_webrtc import webrtc_streamer, WebRtcMode, AudioProcessorBase  # type: ignore
except Exception:  # noqa: BLE001
    webrtc_streamer = None  # type: ignore
    WebRtcMode = None  # type: ignore
    class AudioProcessorBase:  # type: ignore
        pass

# ---------------------------------------------------------------------------
# Persistence (puede no existir en modo aislado)
try:  # pragma: no cover - fallback silencioso
    from backend.src.utils.persistence import store  # type: ignore
except Exception:  # noqa: BLE001
    store = None  # type: ignore

# Servidores locales opcionales (echo & elevenlabs sim)
try:
    from backend.src.mcp.echo_server import serve_in_thread as _echo_serve  # type: ignore
except Exception:  # noqa: BLE001
    _echo_serve = None
try:  # ElevenLabs sim
    from backend.src.mcp.elevenlabs_server import serve_in_thread as _el_serve  # type: ignore
except Exception:  # noqa: BLE001
    _el_serve = None

# ElevenLabs integration (STT/TTS)
try:
    from backend.src.integrations.elevenlabs import ElevenLabsClient  # type: ignore
except Exception:  # noqa: BLE001
    ElevenLabsClient = None  # type: ignore

# Mistral Agent (LLM)
try:
    from backend.src.agents.mistral_agent import MistralAgent, MistralAgentConfig  # type: ignore
except Exception:  # noqa: BLE001
    MistralAgent, MistralAgentConfig = None, None  # type: ignore

st.set_page_config(page_title="CeroDolor - Chequeo Diario", page_icon="🩺")

# Accessibility: ensure document language is Spanish for screen readers
try:  # pragma: no cover
        _html("<script>document.documentElement.lang='es';</script>", height=0)
except Exception:
        pass

# CSS opcional
try:  # pragma: no cover
    with open("frontend/styles/empathy-agent.css", "r", encoding="utf-8") as _f:
        st.markdown(f"<style>{_f.read()}</style>", unsafe_allow_html=True)
except Exception:  # noqa: BLE001
    pass

# Design tokens and accessibility-focused overrides
st.markdown(
        """
        <style>
        :root {
            --cdp-accent: #2563eb; /* calm blue */
            --cdp-accent-600: #1d4ed8;
            --cdp-danger: #dc2626; /* reserved for errors and very high pain */
            --cdp-bg: #ffffff;
            --cdp-muted: #f6f7f8;
            --cdp-border: #e5e7eb;
            --cdp-text: #111827;
            --cdp-space-1: 8px;  --cdp-space-2: 16px;  --cdp-space-3: 24px;  --cdp-space-4: 32px;
            --cdp-radius: 10px;
        }
        .main .block-container { max-width: 1200px; }
        .empathy-agent-page.cd-container { padding-top: var(--cdp-space-2); }
            /* Typography ramp */
            h1 { font-size: 2.25rem; line-height: 1.2; }
            h2 { font-size: 1.5rem; line-height: 1.3; }
            h3 { font-size: 1.2rem; line-height: 1.3; }
            @media (max-width: 640px) {
                h1 { font-size: 1.75rem; }
                h2 { font-size: 1.25rem; }
                h3 { font-size: 1.1rem; }
            }
            /* Reduce motion when user prefers */
            @media (prefers-reduced-motion: reduce) {
                * { animation: none !important; transition: none !important; }
            }
        /* Tab active state with clearer underline */
        .stTabs [role="tab"][aria-selected="true"] {
            border-bottom: 3px solid var(--cdp-accent) !important;
            color: var(--cdp-text) !important;
        }
        /* Buttons hierarchy */
        .stButton > button[kind="primary"], .stButton > button[data-baseweb] {
            background: var(--cdp-accent) !important; border-color: var(--cdp-accent-600) !important;
        }
        .stButton > button:hover { filter: brightness(0.97); }
        /* Focus visibility across controls */
        button:focus-visible, input:focus-visible, textarea:focus-visible, [role="tab"]:focus-visible, [role="button"]:focus-visible {
            outline: 3px solid var(--cdp-accent) !important; outline-offset: 2px !important;
        }
        /* Muted cards / info blocks */
        .cd-card-muted { background: var(--cdp-muted); border: 1px solid var(--cdp-border); border-radius: var(--cdp-radius); padding: var(--cdp-space-2); }
        /* Status badge */
        .cd-status { float: right; padding: 4px 10px; border-radius: 999px; font-size: 12px; border:1px solid var(--cdp-border); }
        .cd-status.ok { background:#ecfdf5; color:#065f46; }
        .cd-status.warn { background:#fffbeb; color:#92400e; }
        .cd-status.err { background:#fef2f2; color:#991b1b; }
        /* Sparkline bars */
        .cd-sparkline { display:flex; gap:2px; align-items:flex-end; height:40px; }
        .cd-sparkline span { display:inline-block; width:6px; background: var(--cdp-accent); border-radius:2px; }
        /* Hide developer main menu for end users (optional) */
        #MainMenu { visibility: hidden; }
        </style>
        """,
        unsafe_allow_html=True,
)

st.markdown('<div class="empathy-agent-page cd-container">', unsafe_allow_html=True)
st.title("Agente de Empatía Crónica")

# --------------- Global health indicator (on-demand) ---------------
def _check_module_health() -> Dict[str, Any]:
    modules = [
        ("aip", "backend.src.agents.aip"),
        ("asd", "backend.src.agents.asd"),
        ("aiper", "backend.src.agents.aiper"),
        ("clinician", "backend.src.agents.clinician_agent"),
        ("patient", "backend.src.agents.patient_agent"),
        ("aic", "backend.src.agents.aic_cli"),
    ]
    results: Dict[str, Any] = {"items": {}, "ok_count": 0, "fail_count": 0}
    for name, mod in modules:
        try:
            res = _run_subprocess([sys.executable, "-m", mod, "--health"])  # type: ignore
            parsed = res.get("parsed") if isinstance(res, dict) else None
            ok = False
            if isinstance(parsed, dict):
                ok = bool(parsed.get("ok")) and (parsed.get("data", {}).get("online", True) is not False)
            results["items"][name] = {"ok": ok, "raw": parsed or res.get("stdout")}
            if ok:
                results["ok_count"] += 1
            else:
                results["fail_count"] += 1
        except Exception:
            results["items"][name] = {"ok": False, "raw": None}
            results["fail_count"] += 1
    results["ts"] = datetime.utcnow().isoformat()
    return results

def _render_status_badge() -> None:
    mh = st.session_state.get("module_health")
    if not mh:
        st.markdown('<span class="cd-status warn">Sistema: Desconocido</span>', unsafe_allow_html=True)
        return
    okc = int(mh.get("ok_count", 0)); fc = int(mh.get("fail_count", 0))
    if fc == 0 and okc > 0:
        cls = "ok"; label = f"Sistema: OK ({okc})"
    elif okc == 0:
        cls = "err"; label = "Sistema: Offline"
    else:
        cls = "warn"; label = f"Sistema: Degradado ({okc}/{okc+fc})"
    st.markdown(f'<span class="cd-status {cls}">{label}</span>', unsafe_allow_html=True)

col_head_l, col_head_r = st.columns([6, 2])
with col_head_r:
    if st.button("Actualizar estado", help="Ejecuta chequeos de salud de módulos", key="btn_health_refresh"):
        with st.spinner("Chequeando módulos…"):
            st.session_state.module_health = _check_module_health()
    _render_status_badge()
with col_head_l:
    # Patient quick pill
    st.markdown(
        f"<span class='cd-status ok' title='Paciente actual'>ID: {st.session_state.get('patient_id','-')}</span>",
        unsafe_allow_html=True,
    )
    
# Optional details of system status
if st.session_state.get("module_health"):
    with st.expander("Estado del sistema (detalles)"):
        st.json(st.session_state.get("module_health"))

# Auto-generate a random patient id if none present (one per browser session)
if "patient_id" not in st.session_state or not st.session_state.get("patient_id"):
    st.session_state["patient_id"] = f"patient_{secrets.token_hex(4)}"

# Preferencias persistentes por paciente
PREFS_PATH = Path("backend/sessions/_prefs.json")

def _ensure_prefs_dir() -> None:
    try:
        PREFS_PATH.parent.mkdir(parents=True, exist_ok=True)
    except Exception:  # noqa: BLE001
        pass

def _load_all_prefs() -> Dict[str, Any]:
    try:
        if PREFS_PATH.exists():
            return json.loads(PREFS_PATH.read_text(encoding="utf-8") or "{}")
    except Exception:  # noqa: BLE001
        pass
    return {}

def _save_patient_prefs(pid: str, prefs: Dict[str, Any]) -> None:
    _ensure_prefs_dir()
    allp = _load_all_prefs()
    allp[pid] = prefs
    try:
        PREFS_PATH.write_text(json.dumps(allp, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass

def _apply_saved_prefs(pid: str) -> None:
    saved = _load_all_prefs().get(pid) or {}
    # Only set if not already chosen in this session
    for k, v in saved.items():
        if k not in st.session_state:
            st.session_state[k] = v

TAB_CHEQUEO, TAB_PROGRESO, TAB_AVANZADO = st.tabs(["Chequeo Diario", "Progreso", "Avanzado"])

# ---------------------------------------------------------------------------
# Helpers

class AudioBufferProcessor(AudioProcessorBase):  # streamlit-webrtc audio processor
    def __init__(self) -> None:
        self.chunks: List[bytes] = []
        self.sample_rate: int | None = None
        self.channels: int | None = None
        self.level: float = 0.0  # 0..1 RMS approx
        self.frames: int = 0
        self.clip_events: int = 0
        self.level_history: List[float] = []

    def recv_audio(self, frame):  # type: ignore[no-untyped-def]
        try:
            import numpy as np  # local import to avoid dependency at import time
            # Convert to signed 16-bit PCM ndarray
            arr = frame.to_ndarray(format="s16")  # shape: (channels, samples)
            self.sample_rate = getattr(frame, "sample_rate", self.sample_rate) or 48000
            if arr.ndim == 2:
                self.channels = arr.shape[0]
                # Compute RMS level across all channels
                rms = float(np.sqrt(np.mean((arr.astype(np.int32)) ** 2))) / 32768.0
                self.level = float(max(0.0, min(1.0, rms)))
                pcm_bytes = arr.tobytes(order="C")
                self.frames += arr.shape[1]
            else:
                self.channels = 1
                pcm = arr.astype(np.int16)
                rms = float(np.sqrt(np.mean((pcm.astype(np.int32)) ** 2))) / 32768.0
                self.level = float(max(0.0, min(1.0, rms)))
                pcm_bytes = pcm.tobytes(order="C")
                self.frames += pcm.shape[0]
            self.chunks.append(pcm_bytes)
            # clipping heuristic: rms > 0.9
            if self.level > 0.9:
                self.clip_events += 1
            # Keep small history for waveform-ish display
            self.level_history.append(self.level)
            if len(self.level_history) > 60:
                self.level_history = self.level_history[-60:]
        except Exception:
            # On any failure, skip frame
            pass

    def get_wav_bytes(self) -> bytes:
        if not self.chunks:
            return b""
        sr = int(self.sample_rate or 48000)
        ch = int(self.channels or 1)
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(ch)
            wf.setsampwidth(2)  # 16-bit
            wf.setframerate(sr)
            wf.writeframes(b"".join(self.chunks))
        return buf.getvalue()

    def reset(self) -> None:
        self.chunks.clear()
        self.level = 0.0
        self.frames = 0
        self.clip_events = 0
        self.level_history.clear()


def _get_or_create_audio_proc() -> AudioBufferProcessor:
    """Return a session-scoped AudioBufferProcessor, creating it if missing.

    Streamlit may rerun scripts frequently; using this guard ensures the
    audio_processor_factory can always obtain a valid instance without raising
    AttributeError: st.session_state has no attribute 'audio_proc'.
    """
    ap = st.session_state.get("audio_proc")
    if not isinstance(ap, AudioBufferProcessor):
        ap = AudioBufferProcessor()
        st.session_state.audio_proc = ap
    return ap

# Ensure the audio processor exists early to avoid racey AttributeError on first use
try:
    if "audio_proc" not in st.session_state:
        st.session_state.audio_proc = AudioBufferProcessor()
except Exception:
    # If session state is not ready yet, it will be created by the factory later
    pass

def _get_el_client() -> Any | None:
    """Singleton-ish ElevenLabs client (real network only if env allows)."""
    if ElevenLabsClient is None:
        return None
    if "el_client" not in st.session_state:
        try:
            st.session_state.el_client = ElevenLabsClient()  # type: ignore
        except Exception:  # noqa: BLE001
            st.session_state.el_client = None
    return st.session_state.get("el_client")

def _el_transcribe_bytes(audio_bytes: bytes, *, language: str = "es") -> str:
    client = _get_el_client()
    if not client:
        return ""
    try:
        res = client.transcribe(audio_bytes, language=language)
        if isinstance(res, dict) and isinstance(res.get("text"), str):
            return str(res.get("text"))
    except Exception:  # noqa: BLE001
        pass
    return ""

def _el_synthesize_text(text: str, *, voice_id: str | None = None, language: str = "es") -> bytes:
    client = _get_el_client()
    if not client:
        return b""

    # Aplicar preferencias guardadas al inicio para el paciente actual
    _apply_saved_prefs(st.session_state.get("patient_id", "demo_patient"))
    try:
        res = client.synthesize(text, voice_id=voice_id, language=language)
        # Prefer audio_b64 if present
        if isinstance(res, dict) and isinstance(res.get("audio_b64"), str):
            try:
                return base64.b64decode(res.get("audio_b64") or "")
            except Exception:  # noqa: BLE001
                return b""
        # Offline simulation case returns a marker string; no playable audio
        return b""
    except Exception:  # noqa: BLE001
        return b""

def _store_patient_context(patient_id: str, pain_level: int, pain_desc: str, mood: str, sleep: str) -> None:
    st.session_state["patient_id"] = patient_id
    st.session_state["patient_ctx"] = {
        "patient_id": patient_id,
        "pain_level": pain_level,
        "pain_desc": pain_desc,
        "mood": mood,
        "sleep": sleep,
    }


def _run_subprocess(args: List[str]) -> Dict[str, Any]:
    """Run a Python subprocess returning {success, stdout, stderr, parsed?}."""
    try:
        proc = subprocess.run(args, capture_output=True, text=True, check=True)
        out = proc.stdout
        parsed = None
        try:
            parsed = json.loads(out)
        except Exception:  # noqa: BLE001
            pass
        return {"success": True, "stdout": out, "stderr": proc.stderr, "parsed": parsed}
    except subprocess.CalledProcessError as e:  # noqa: BLE001
        return {"success": False, "stdout": e.stdout, "stderr": e.stderr}


def _session_pain_stats(pid: str) -> Dict[str, Any] | None:
    """Compute simple pain stats from persisted events.

    Returns None si no hay eventos de dolor.
    Campos: last, mean_last_3, mean_last_7, delta_last, pct_change_last, anomaly, severity_trend, count.
    """
    if not store:
        return None
    sess = store.get(pid)
    pain_events = [e for e in sess.events if e.get("type") == "pain_registration"]  # type: ignore
    vals: List[int] = []
    for ev in pain_events:
        data = ev.get("data", {}).get("pain", {})  # type: ignore
        if isinstance(data, dict):
            v = data.get("level") or data.get("pain_level") or data.get("value")
            if isinstance(v, (int, float)):
                vals.append(int(v))
    if not vals:
        return None
    last = vals[-1]
    last_3 = vals[-3:]
    last_7 = vals[-7:]
    mean3 = round(mean(last_3), 2)
    mean7 = round(mean(last_7), 2)
    delta_last = last - (vals[-2] if len(vals) > 1 else last)
    base_prev = mean7 if len(vals) > 1 else last
    pct_change_last = round(((last - base_prev) / base_prev) * 100, 2) if base_prev else 0.0
    # Anomaly very naive: jump >=3 or pct_change > 40%
    anomaly = abs(delta_last) >= 3 or abs(pct_change_last) >= 40
    # Trend (last up to 3 deltas)
    if len(vals) >= 3:
        seq = vals[-3:]
        if seq[0] > seq[1] > seq[2]:
            severity_trend = "down"
        elif seq[0] < seq[1] < seq[2]:
            severity_trend = "up"
        else:
            severity_trend = "flat"
    else:
        severity_trend = "flat"
    return {
        "last": last,
        "mean_last_3": mean3,
        "mean_last_7": mean7,
        "delta_last": delta_last,
        "pct_change_last": pct_change_last,
        "anomaly": anomaly,
        "severity_trend": severity_trend,
        "count": len(vals),
    }


def _sparkline(vals: List[int]) -> str:
    if not vals:
        return ""
    max_v = max(vals) or 1
    bars = []
    for v in vals:
        h = max(4, int((v / max_v) * 36))
        bars.append(f"<span style='height:{h}px' title='{v}'></span>")
    return "<div class='cd-sparkline'>" + "".join(bars) + "</div>"


def _toast(msg: str, icon: str = "✅") -> None:
    """Toast if available, else fall back to success/info."""
    try:
        if hasattr(st, "toast"):
            st.toast(msg, icon=icon)  # type: ignore[attr-defined]
        else:
            st.success(msg)
    except Exception:
        try:
            st.info(msg)
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Inicializar servidores locales una sola vez
if _echo_serve and "echo_server" not in st.session_state:
    httpd, thread, port = _echo_serve(0)
    st.session_state.echo_server = {"httpd": httpd, "thread": thread, "port": port, "base_url": f"http://127.0.0.1:{port}"}
if _el_serve and "el_server" not in st.session_state:
    httpd, thread, port = _el_serve(0)
    st.session_state.el_server = {"httpd": httpd, "thread": thread, "port": port, "base_url": f"http://127.0.0.1:{port}"}

if "conversation_turns" not in st.session_state:
    st.session_state.conversation_turns = []
if "log" not in st.session_state:
    st.session_state.log = []

# ---------------------------------------------------------------------------
# TAB 1: Chequeo Diario
with TAB_CHEQUEO:
    st.markdown("## Tu Chequeo Diario")
    st.caption("Registra tu dolor, habla con el agente y recibe una sugerencia personalizada.")

    # ---------------- Voz en vivo (micrófono) ----------------
    with st.expander("🎙️ Captura de Voz en Vivo (Beta)", expanded=False):
        # Privacy badge if user disabled WAV persistence
        if bool(st.session_state.get("pref_privacy_no_wav")):
            st.caption("🔒 Privacidad activa: no se guardarán archivos WAV en disco.")
        if os.getenv("CERODOLOR_ENABLE_WEBRTC", "1") not in {"1", "true", "True"}:
            st.info("WebRTC deshabilitado por entorno (CERODOLOR_ENABLE_WEBRTC=0). Usa el cargador de archivo.")
        elif webrtc_streamer is None:
            st.info(
                "'streamlit-webrtc' no instalado o falló la importación. "
                "Instala con: pip install streamlit-webrtc (reinicia la app). "
                "Mientras tanto, usa el cargador de archivo."
            )
        else:
            st.caption("Pulsa START para hablar. Al detener, transcribimos con ElevenLabs si está habilitado, con fallback local.")
            ctx_live = None
            if WebRtcMode is not None:
                # Inicializar procesador en el estado
                _get_or_create_audio_proc()
                # Lanzar streamer con procesador de audio custom
                ctx_live = webrtc_streamer(  # type: ignore[arg-type]
                    key="cd-live-audio",
                    mode=WebRtcMode.SENDONLY,
                    audio_receiver_size=256,
                    media_stream_constraints={"audio": True, "video": False},
                    audio_processor_factory=_get_or_create_audio_proc,  # type: ignore[arg-type]
                )
                # Indicadores de estado conversacional
                c_status, c_meter, c_timer = st.columns([1, 2, 1])
                if ctx_live and ctx_live.state.playing:
                    c_status.success("Grabando…")
                    if bool(st.session_state.get("pref_privacy_no_wav")):
                        st.caption("Privacidad activa: no se guardará el WAV en disco al finalizar.")
                    # simple peak meter based on last RMS
                    lvl = float(getattr(st.session_state.get("audio_proc"), "level", 0.0))
                    bar = "█" * int(lvl * 20)
                    c_meter.code(f"Nivel: {lvl:0.2f}  {bar}")
                    if "rec_started_ts" not in st.session_state:
                        st.session_state.rec_started_ts = time.time()
                    secs = int(time.time() - st.session_state.get("rec_started_ts", time.time()))
                    c_timer.metric("Segundos", secs)
                    # Mostrar clipping y mini-historial
                    clips = int(getattr(st.session_state.get("audio_proc"), "clip_events", 0))
                    st.caption(f"Clips: {clips}")
                    hist = getattr(st.session_state.get("audio_proc"), "level_history", [])
                    if hist:
                        hist_str = "".join("▁▂▃▄▅▆▇"[min(6, int(h*6))] for h in hist)
                        st.code(hist_str)
                else:
                    c_status.info("Inactivo")
                    c_meter.caption("Nivel: 0.00")
                    c_timer.metric("Segundos", 0)

                # Transcribir cuando se detiene
                if "rec_active_prev" not in st.session_state:
                    st.session_state.rec_active_prev = False
                current_active = bool(ctx_live and ctx_live.state.playing)
                previously_active = bool(st.session_state.get("rec_active_prev"))
                if previously_active and not current_active:
                    # Se acaba de detener: construir WAV y transcribir
                    _ap = _get_or_create_audio_proc()
                    wav_bytes = _ap.get_wav_bytes()
                    _ap.reset()
                    st.session_state.rec_started_ts = time.time()
                    if wav_bytes:
                        st.info("Transcribiendo audio grabado…")
                        vt = ""
                        try:
                            if bool(st.session_state.get("pref_el")):
                                vt = _el_transcribe_bytes(wav_bytes)
                            if not vt:
                                from backend.src.services.aip_service import stt_transcribe_file  # type: ignore
                                # Guardar temporalmente para el fallback basado en archivo
                                tmp_wav = Path("temp_webrtc_clip.wav")
                                tmp_wav.write_bytes(wav_bytes)
                                vt = stt_transcribe_file(str(tmp_wav)) or ""
                                try:
                                    tmp_wav.unlink(missing_ok=True)
                                except Exception:
                                    pass
                        except Exception:  # noqa: BLE001
                            vt = ""
                        if vt:
                            existing = st.session_state.get("voice_transcript") or ""
                            sep = "\n" if existing else ""
                            st.session_state.voice_transcript = f"{existing}{sep}{vt}"
                            st.success("Transcripción añadida desde WebRTC.")
                            # Persistencia de evento y guardado de WAV como archivo temporal ligado a paciente
                            if store is not None:
                                try:
                                    pid_ev = st.session_state.get("patient_id", "demo_patient")
                                    # Guardar wav a disco para trazabilidad salvo si privacidad lo impide
                                    if not bool(st.session_state.get("pref_privacy_no_wav")):
                                        wav_path = Path(f"backend/sessions/{pid_ev}_last.wav")
                                        wav_path.write_bytes(wav_bytes)
                                        store.append_event(pid_ev, "voice_transcript", {"text": vt, "source": "webrtc_final", "wav_path": str(wav_path)})
                                    else:
                                        store.append_event(pid_ev, "voice_transcript", {"text": vt, "source": "webrtc_final"})
                                except Exception:
                                    pass
                        else:
                            st.warning("No se pudo transcribir el audio.")
                st.session_state.rec_active_prev = current_active

                # STT parcial cada ~5s mientras está grabando (opcional, best-effort)
                if current_active:
                    last_partial = float(st.session_state.get("last_partial_ts", 0.0))
                    if time.time() - last_partial > 5.0 and st.session_state.get("audio_proc") is not None:
                        # Tomar snapshot de lo acumulado (sin reset) para un feedback ligero
                        wav_partial = _get_or_create_audio_proc().get_wav_bytes()
                        if wav_partial and len(wav_partial) > 4096:
                            try:
                                vt_p = ""
                                if bool(st.session_state.get("pref_el")):
                                    vt_p = _el_transcribe_bytes(wav_partial)
                                if vt_p:
                                    st.caption(f"Parcial: {vt_p[:64]}…")
                                    # Persistencia del parcial
                                    if store is not None:
                                        try:
                                            pid_ev = st.session_state.get("patient_id", "demo_patient")
                                            store.append_event(pid_ev, "voice_transcript_partial", {"text": vt_p, "source": "webrtc_partial"})
                                        except Exception:
                                            pass
                                st.session_state.last_partial_ts = time.time()
                            except Exception:
                                pass
            else:
                st.info("WebRtcMode no disponible; intenta reiniciar o actualizar streamlit-webrtc.")
            if ctx_live and ctx_live.state.playing:
                st.write("Grabando… (los bytes de audio no se guardan todavía)")
            if st.button("Simular transcripción (usar audio en memoria)"):
                # Placeholder: en futuro enviaríamos buffer a STT real
                pseudo_text = "(Sim) He tenido dolor moderado hoy, peor al levantarme. Dormí mal."  # deterministic
                st.session_state.voice_transcript = (
                    (st.session_state.get("voice_transcript") or "") + ("\n" if st.session_state.get("voice_transcript") else "") + pseudo_text
                )
                st.success("Transcripción simulada añadida.")

    with st.expander("⚙️ Preferencias", expanded=False):
        st.session_state.pref_voice = st.selectbox("Voz preferida", ["demo_female", "demo_male", "suave"], index=0)
        st.session_state.pref_autoplay = st.checkbox(
            "Reproducir respuestas automáticamente", value=st.session_state.get("pref_autoplay", True)
        )
        st.session_state.pref_privacy_no_wav = st.checkbox(
            "No guardar archivos WAV de capturas en disco (privacidad)",
            value=bool(st.session_state.get("pref_privacy_no_wav", False)),
            help="Si está activo, el audio capturado en vivo no se persistirá como archivo .wav en backend/sessions/."
        )
        st.session_state.pref_el = st.checkbox(
            "Usar ElevenLabs para voz (requiere ELEVENLABS_API_KEY y USE_NETWORK=true)",
            value=bool(st.session_state.get("pref_el", False)),
            help="Si está activo, intentaremos STT/TTS con ElevenLabs y haremos fallback local si falla."
        )
        if st.session_state.pref_el:
            st.session_state.pref_el_voice = st.text_input(
                "ElevenLabs Voice ID (opcional)", value=st.session_state.get("pref_el_voice", ""),
                help="Si se deja vacío usará el valor del entorno ELEVENLABS_TTS_VOICE_ID o el default de la API."
            )
        # Mistral preferences
        st.session_state.pref_use_mistral = st.checkbox(
            "Usar Mistral para sugerencias (requiere MISTRAL_API_KEY y USE_NETWORK=true)",
            value=bool(st.session_state.get("pref_use_mistral", False)),
            help="Si está activo, las sugerencias se generarán con Mistral en vez del orquestador local (con fallback)."
        )
        if st.session_state.get("pref_use_mistral"):
            st.session_state.pref_mistral_model = st.text_input(
                "Modelo Mistral", value=st.session_state.get("pref_mistral_model", os.getenv("MISTRAL_MODEL", "mistral-large-latest"))
            )
            st.session_state.pref_mistral_temp = st.slider(
                "Temperatura Mistral", 0.0, 1.0, float(st.session_state.get("pref_mistral_temp", float(os.getenv("MISTRAL_TEMPERATURE", "0.4"))))
            )
        colp1, colp2 = st.columns([1,1])
        if colp1.button("Guardar preferencias (paciente)"):
            pid_for_prefs = st.session_state.get("patient_id", "demo_patient")
            prefs = {
                "pref_voice": st.session_state.get("pref_voice"),
                "pref_autoplay": bool(st.session_state.get("pref_autoplay")),
                "pref_privacy_no_wav": bool(st.session_state.get("pref_privacy_no_wav")),
                "pref_el": bool(st.session_state.get("pref_el")),
                "pref_el_voice": st.session_state.get("pref_el_voice", ""),
                "pref_use_mistral": bool(st.session_state.get("pref_use_mistral")),
                "pref_mistral_model": st.session_state.get("pref_mistral_model"),
                "pref_mistral_temp": float(st.session_state.get("pref_mistral_temp", 0.4)),
            }
            _save_patient_prefs(pid_for_prefs, prefs)
            _toast("Preferencias guardadas.")
        if colp2.button("Probar voz"):
            demo_text = "Esta es una prueba de voz del agente."
            audio_demo = b""
            audio_demo_mime = "audio/wav"
            if bool(st.session_state.get("pref_el")):
                audio_demo = _el_synthesize_text(demo_text, voice_id=(st.session_state.get("pref_el_voice") or None))
                if audio_demo:
                    # ElevenLabs typically returns MP3/OGG; default to MPEG unless RIFF header found
                    audio_demo_mime = "audio/mpeg" if not audio_demo.startswith(b"RIFF") else "audio/wav"
            if not audio_demo:
                try:
                    from backend.src.services.aip_service import tts_generate_bytes  # type: ignore
                    audio_demo = tts_generate_bytes(demo_text, st.session_state.get("pref_voice")) or b""
                except Exception:  # noqa: BLE001
                    audio_demo = b""
            if audio_demo:
                st.audio(audio_demo, format=audio_demo_mime)
                _toast("Reproduciendo prueba de voz")
            else:
                st.warning("No fue posible sintetizar la prueba de voz.")

    patient_id = st.text_input(
        "ID del paciente", value=str(st.session_state.get("patient_id", "demo_patient") or "demo_patient")
    )
    col_left, col_right = st.columns([2, 1])
    with col_left:
        pain_level = st.slider(
            "Nivel de dolor (1-10)", 1, 10, st.session_state.get("patient_ctx", {}).get("pain_level", 5)
        )
        # Live severity badge (uses semantic colors)
        _sev = "leve" if pain_level <= 3 else ("moderado" if pain_level <= 6 else "alto")
        _sev_cls = "ok" if _sev == "leve" else ("warn" if _sev == "moderado" else "err")
        st.markdown(f"<span class='cd-status {_sev_cls}'>Severidad: {_sev}</span>", unsafe_allow_html=True)
        pain_desc = st.text_area(
            "Describe tu dolor (o cambios)",
            st.session_state.get("patient_ctx", {}).get("pain_desc", "punzante en la espalda baja"),
        )
        mood = st.text_input("Estado de ánimo", st.session_state.get("patient_ctx", {}).get("mood", "ansioso"))
        sleep = st.text_input("Sueño", st.session_state.get("patient_ctx", {}).get("sleep", "mal"))
    with col_right:
        st.markdown("### Voz")
        uploaded_voice = st.file_uploader(
            "Clip de voz",
            type=["wav", "mp3", "m4a", "ogg"],
            help="Arrastra un archivo de audio corto (≤ 5 min). Formatos: WAV/MP3/M4A/OGG."
        )  # demo
        btn_transcribe = st.button("Transcribir clip", disabled=uploaded_voice is None)
        if btn_transcribe and uploaded_voice:
            tmp = Path("temp_voice_clip.bin")
            tmp.write_bytes(uploaded_voice.read())
            # Preferir ElevenLabs STT si el usuario así lo indicó
            vt = ""
            try:  # pragma: no cover
                if bool(st.session_state.get("pref_el")):
                    el_text = _el_transcribe_bytes(tmp.read_bytes())
                    if el_text:
                        vt = el_text
                if not vt:
                    from backend.src.services.aip_service import stt_transcribe_file  # type: ignore
                    vt = stt_transcribe_file(str(tmp)) or ""
            except Exception:  # noqa: BLE001
                try:
                    from backend.src.services.aip_service import stt_transcribe_file  # type: ignore
                    vt = stt_transcribe_file(str(tmp)) or ""
                except Exception:  # noqa: BLE001
                    vt = ""
            st.session_state.voice_transcript = vt
            try:
                tmp.unlink(missing_ok=True)
            except Exception:  # noqa: BLE001
                pass
            if vt:
                _toast("Transcripción añadida desde archivo")
        if st.session_state.get("voice_transcript"):
            st.text_area("Transcripción", st.session_state.get("voice_transcript"), height=120)
            if st.button("Borrar transcripción de voz"):
                # Persistir evento de borrado (respetar privacidad)
                if store is not None:
                    try:
                        store.append_event(patient_id, "voice_transcript_cleared", {"reason": "user_action"})
                    except Exception:
                        pass
                st.session_state.voice_transcript = ""
                st.session_state.last_summary = None
                st.session_state.last_summary_src = None
                try:
                    st.rerun()
                except Exception:
                    pass
            st.caption("Se añadirá al análisis.")
            # Summarize transcript once per change
            changed = st.session_state.get("last_summary_src") != st.session_state.get("voice_transcript")
            if changed:
                try:
                    from backend.src.services.conversation_service import summarize_transcript  # type: ignore
                    summary = summarize_transcript(st.session_state.get("voice_transcript", ""))
                    st.session_state.last_summary_src = st.session_state.get("voice_transcript")
                    st.session_state.last_summary = summary.to_dict()
                    if store is not None:
                        try:
                            store.append_event(patient_id, "transcript_summary", {"summary": summary.to_dict()})
                            # Persist raw transcript snapshot (lightweight) once per change
                            store.append_event(patient_id, "voice_transcript", {"text": st.session_state.get("voice_transcript", "")})
                        except Exception:  # noqa: BLE001
                            pass
                except Exception:  # noqa: BLE001
                    st.session_state.last_summary = None
            s = st.session_state.get("last_summary")
            if isinstance(s, dict):
                with st.expander("Resumen de transcripción detectado"):
                    st.write(s)
                    # Prefill fields if empty
                    mood_hint = s.get("mood_hint") if isinstance(s.get("mood_hint"), str) else None
                    sleep_quality = s.get("sleep_quality") if isinstance(s.get("sleep_quality"), str) else None
                    if not mood and mood_hint:
                        st.info("Se detectó pista de ánimo: rellenando campo.")
                        mood = mood_hint or mood
                    if not sleep and sleep_quality in {"good", "bad", "regular"}:
                        sleep = sleep_quality or sleep

    # ---------------- Diálogo guiado opcional ----------------
    with st.expander("Diálogo Guiado (Beta)", expanded=False):
        guide_active = st.checkbox("Activar guía de preguntas", value=False)
        if guide_active:
            if "guided_asked_categories" not in st.session_state:
                st.session_state.guided_asked_categories = []
            if "guide_answers" not in st.session_state:
                st.session_state.guide_answers = []
            # Derive adherence (reuse stats) and summary if present
            stats = _session_pain_stats(patient_id)
            adherence = None  # (placeholder: can compute if needed later)
            summary_dict = st.session_state.get("last_summary") if isinstance(st.session_state.get("last_summary"), dict) else None
            try:
                from backend.src.services.guidance_service import next_guided_question  # type: ignore
            except Exception:
                next_guided_question = None  # type: ignore
            chosen = None
            if next_guided_question:
                try:
                    asked_categories = [
                        str(g.get("category"))
                        for g in st.session_state.get("guide_answers", [])
                        if isinstance(g, dict) and isinstance(g.get("category"), str)
                    ]
                    chosen = next_guided_question(
                        patient_id=patient_id,
                        asked_categories=asked_categories,
                        stats=stats,
                        summary=summary_dict,
                        adherence=adherence,
                    )
                except Exception:  # noqa: BLE001
                    chosen = None
            if chosen and chosen.get("question"):
                st.info(chosen.get("question"))
                resp = st.text_input("Respuesta", key=f"guide_resp_{len(st.session_state.get('guide_answers', []))}")
                if st.button("Guardar respuesta", key=f"guide_btn_{len(st.session_state.get('guide_answers', []))}"):
                    all_r = st.session_state.get("guide_answers", [])
                    all_r.append({
                        "q": chosen.get("question"),
                        "a": resp,
                        "category": chosen.get("category"),
                        "reason": chosen.get("reason"),
                        "priority": chosen.get("priority"),
                    })
                    st.session_state.guide_answers = all_r
                    if store is not None:
                        try:
                            store.append_event(patient_id, "guided_dialogue", {"q": chosen.get("question"), "a": resp, "category": chosen.get("category")})
                        except Exception:  # noqa: BLE001
                            pass
                    try:
                        st.rerun()
                    except Exception:  # noqa: BLE001
                        pass
            else:
                st.success("Guía completada o no hay más preguntas de valor.")
            # Display previous answers
            if st.session_state.get("guide_answers"):
                with st.expander("Respuestas Guiadas Acumuladas"):
                    for ga in st.session_state.get("guide_answers", [])[-8:]:  # limit view
                        st.write(f"- {ga.get('q')}\n  → {ga.get('a')}")
        # Ensamblar texto de guía dentro de la descripción si procede durante Procesar

    if st.button("Procesar", type="primary", use_container_width=True):
        st.session_state["patient_id"] = patient_id
        with st.spinner("Analizando y generando sugerencia…"):
            merged_desc = pain_desc or "(sin descripcion)"
            if st.session_state.get("voice_transcript"):
                merged_desc += f"\n[VOZ]: {st.session_state.voice_transcript}"
            # Integrar guía al texto
            if st.session_state.get("guide_answers"):
                guide_text = "\n".join(f"[PREGUNTA] {ga['q']}\n[RESPUESTA] {ga['a']}" for ga in st.session_state.get("guide_answers", []))
                merged_desc += f"\n[GUIA]\n{guide_text}"
            suggestion: str = ""
            intervention_type: str = "general"
            intervention_details: Dict[str, Any] = {}
            last_level = int(pain_level)
            severity = "leve" if last_level <= 3 else ("moderado" if last_level <= 6 else "alto")

            use_mistral = bool(st.session_state.get("pref_use_mistral")) and (MistralAgent is not None)
            cycle: Dict[str, Any] = {}
            if use_mistral:
                try:
                    cfg = MistralAgentConfig(
                        model=st.session_state.get("pref_mistral_model", os.getenv("MISTRAL_MODEL", "mistral-large-latest")),
                        temperature=float(st.session_state.get("pref_mistral_temp", float(os.getenv("MISTRAL_TEMPERATURE", "0.4")))),
                    ) if MistralAgentConfig else None
                    if "m_agent" not in st.session_state:
                        st.session_state.m_agent = MistralAgent(cfg)  # type: ignore
                    prompt = (
                        f"Paciente: {patient_id}\n"
                        f"Dolor (1-10): {pain_level}\n"
                        f"Ánimo: {mood or 'neutral'}\nSueño: {sleep or 'regular'}\n"
                        "Contexto:\n" + merged_desc + "\n\n"
                        "Genera UNA sugerencia concreta y empática (máx 2 frases) con un tipo entre: breathing, movement, mindfulness, education, reinforcement, general."
                    )
                    res = st.session_state.m_agent.ask(prompt)  # type: ignore
                    suggestion = res.get("text") or "Mantén movilidad suave y respiración diafragmática."
                    intervention_type = "llm_suggestion"
                    cycle = {"mistral": {"prompt": prompt, "response": res}}
                    # Capture trace id if present
                    try:
                        trace_id = res.get("meta", {}).get("trace_id") if isinstance(res, dict) else None
                        if trace_id:
                            st.session_state["last_trace_id"] = trace_id
                    except Exception:
                        pass
                except Exception as e:
                    st.warning(f"Fallo Mistral, usando orquestador local: {e}")
            if not suggestion:
                try:  # pragma: no cover - UI runtime
                    # Import types to satisfy static analysis
                    from backend.src.agents.orchestrator import run_patient_cycle, PatientInput as _PatientInput  # type: ignore
                    from typing import Any as _Any  # local alias
                    patient_payload: _PatientInput = {
                        "patient_id": str(patient_id),
                        "pain_level": int(pain_level),
                        "pain_desc": str(merged_desc),
                        "mood": str(mood or "neutral"),
                        "sleep": str(sleep or "regular"),
                    }
                    cycle = run_patient_cycle(patient_payload, include_report=False)  # type: ignore[assignment]
                    aip_pain = cycle.get("aip", {}).get("pain", {}) if isinstance(cycle, dict) else {}
                    last_level = aip_pain.get("level", pain_level)
                    severity = "leve" if last_level <= 3 else ("moderado" if last_level <= 6 else "alto")
                    aiper_block = cycle.get("aiper", {}) if isinstance(cycle, dict) else {}
                    suggestion = aiper_block.get("suggestion") or "Mantén movilidad suave y respiración diafragmática."
                    intervention_type = aiper_block.get("intervention_type") or "general"
                    intervention_details = aiper_block.get("details") or {}
                except Exception as e:  # noqa: BLE001
                    st.error(f"Error ejecutando ciclo: {e}")
                    cycle = {}
            st.session_state.conversation_turns.append({"role": "user", "text": merged_desc, "pain": last_level})
            st.session_state.conversation_turns.append({
                "role": "agent",
                "text": suggestion,
                "severity": severity,
                "intervention_type": intervention_type,
            })
            audio_bytes = b""
            audio_mime = "audio/wav"
            # Preferir ElevenLabs TTS si el usuario así lo indicó (requiere USE_NETWORK y API Key)
            preferred_voice = st.session_state.get("pref_voice")
            custom_voice_id = (st.session_state.get("pref_el_voice") or None) if bool(st.session_state.get("pref_el")) else None
            el_audio = b""
            if bool(st.session_state.get("pref_el")):
                el_audio = _el_synthesize_text(suggestion, voice_id=custom_voice_id)
            if el_audio:
                audio_bytes = el_audio
                audio_mime = "audio/mpeg" if not el_audio.startswith(b"RIFF") else "audio/wav"
            else:
                try:
                    from backend.src.services.aip_service import tts_generate_bytes  # type: ignore
                    audio_bytes = tts_generate_bytes(suggestion, preferred_voice) or b""
                except Exception:  # noqa: BLE001
                    audio_bytes = b""

        # Spinner finished
        st.success("Procesado")
        c1, c2, c3 = st.columns(3)
        c1.metric("Dolor", last_level)
        c2.metric("Severidad", severity)
        c3.metric("Turnos", len(st.session_state.conversation_turns))
        st.markdown("### Resumen de hoy")
        st.markdown(f"- Nivel de dolor: **{last_level}** ({severity}).")
        if st.session_state.get("voice_transcript"):
            st.markdown("- Incluimos tu voz en el análisis.")
        st.markdown(f"- Sugerencia ({intervention_type}): **{suggestion}**")
        if audio_bytes:
            st.audio(audio_bytes, format=audio_mime)
        # Persistencia mínima
        if store:
            try:
                store.append_event(patient_id, "pain_registration", {"pain": {"level": last_level, "description": pain_desc}})
                store.append_event(patient_id, "mood_sleep", {"mood_sleep": {"mood": mood, "sleep": sleep}})
                details = dict(intervention_details or {})
                # Attach trace id if available
                if st.session_state.get("last_trace_id"):
                    details["trace_id"] = st.session_state.get("last_trace_id")
                store.append_event(
                    patient_id,
                    "intervention",
                    {"suggestion": suggestion, "intervention_type": intervention_type, "details": details},
                )
                if st.session_state.get("guide_answers"):
                    store.append_event(patient_id, "guided_dialogue_summary", {"answers": st.session_state.get("guide_answers")})
            except Exception:  # noqa: BLE001
                pass
        _store_patient_context(patient_id, int(pain_level), pain_desc or "", mood or "", sleep or "")
        if store:
            with st.expander("Detalles analíticos (ocultos)", expanded=False):
                stats = _session_pain_stats(patient_id)
                if stats:
                    st.json({k: stats.get(k) for k in ["last", "mean_last_3", "mean_last_7", "delta_last", "anomaly", "severity_trend"]})
                st.caption("Vista completa en Progreso.")
        with st.expander("Detalle técnico (JSON)"):
            st.code(json.dumps(cycle, ensure_ascii=False, indent=2), language="json")

    if st.session_state.conversation_turns:
        st.markdown("### Conversación Reciente")
        for t in reversed(st.session_state.conversation_turns[-8:]):
            if t.get("role") == "user":
                st.markdown(f"**Tú:** {t.get('text')}")
            else:
                sev = t.get("severity") or "info"
                itype = t.get("intervention_type")
                badge = f" • _{itype}_" if itype else ""
                st.markdown(f"**Agente ({sev}){badge}:** {t.get('text')}")

# ---------------------------------------------------------------------------
# TAB 2: Progreso
with TAB_PROGRESO:
    st.markdown("## Progreso y Tendencias")
    pid = st.session_state.get("patient_id", "demo_patient") or "demo_patient"
    st.caption(f"Paciente actual: {pid}")
    if store:
        sess = store.get(pid)
        stats = _session_pain_stats(pid)
        col_top = st.columns(4)
        if stats:
            col_top[0].metric("Último", stats["last"])
            col_top[1].metric("Media (3)", stats["mean_last_3"])
            col_top[2].metric("Media (7)", stats["mean_last_7"])
            col_top[3].metric("Tendencia", stats.get("severity_trend"))
            anomaly_flag = stats.get("anomaly")
            if anomaly_flag:
                st.warning("Posible anomalía detectada en el último registro.")
        # Sparkline últimos 12
        recent_vals: List[int] = []
        for ev in [e for e in sess.events if e.get("type") == "pain_registration"][-12:]:  # type: ignore
            data = ev.get("data", {}).get("pain", {})  # type: ignore
            if isinstance(data, dict):
                v = data.get("level") or data.get("pain_level") or data.get("value")
                if isinstance(v, (int, float)):
                    recent_vals.append(int(v))
        if recent_vals:
            st.markdown("#### Serie Reciente")
            st.markdown(_sparkline(recent_vals), unsafe_allow_html=True)
        # Adherencia simple
        first_ts = None
        last_ts = None
        try:
            if sess.events:
                first_ts = sess.events[0].get("ts")
                last_ts = sess.events[-1].get("ts")
        except Exception:  # noqa: BLE001
            pass
        days_span = None
        if first_ts and last_ts:
            try:
                dt_first = datetime.fromisoformat(str(first_ts))
                dt_last = datetime.fromisoformat(str(last_ts))
                days_span = max((dt_last - dt_first).days + 1, 1)
            except Exception:  # noqa: BLE001
                pass
        pain_count = len([e for e in sess.events if e.get("type") == "pain_registration"])
        if days_span:
            adherence = round((pain_count / days_span) * 100, 1)
            st.metric("Adherencia (%)", adherence)
        st.markdown("#### Últimas sugerencias")
        sugg_events = [e for e in sess.events if e.get("type") in {"suggestion", "intervention"}][-7:]
        if not sugg_events:
            st.caption("Aún no hay sugerencias.")
            st.info("Registra un nuevo chequeo o activa la captura de voz para recibir una sugerencia personalizada.")
        else:
            for ev in reversed(sugg_events):
                data = ev.get("data") or {}
                text = data.get("suggestion", "") if isinstance(data, dict) else ""
                itype = data.get("intervention_type") if isinstance(data, dict) else None
                if itype:
                    st.write(f"- [{itype}] {text}")
                else:
                    st.write(f"- {text}")
        with st.expander("🗂️ Leyenda Intervenciones"):
            st.caption("Tipos posibles detectados: breathing, movement, mindfulness, education, reinforcement, mixed, llm_suggestion, general")
        with st.expander("🧰 Eventos crudos (últimos 25)"):
            for ev in sess.events[-25:]:  # type: ignore
                st.code(json.dumps(ev, ensure_ascii=False), language="json")
        # Enriched analytics (bootstrap CIs & correlations)
        with st.expander("📈 Analítica Enriquecida", expanded=False):
            try:
                from backend.src.utils.analytics import build_session_enrichment  # type: ignore
                enrichment = build_session_enrichment(sess, seed=42)
                st.json(enrichment)
            except Exception as _e:  # noqa: BLE001
                st.caption("No se pudo generar analítica enriquecida.")
    else:
        # Skeleton placeholders when no persistence/session available
        cols = st.columns(3)
        for c in cols:
            c.caption("")
            c.markdown("<div class='cd-card-muted' style='height:80px'></div>", unsafe_allow_html=True)
        st.caption("La persistencia no está disponible en este entorno. Registra un chequeo para ver tendencias.")

# ---------------------------------------------------------------------------
# TAB 3: Avanzado
with TAB_AVANZADO:
    st.markdown("## Avanzado / Diagnóstico")
    st.caption("Herramientas técnicas para depurar y exportar datos.")
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("### Servidores Locales")
        if _echo_serve and "echo_server" in st.session_state:
            st.success(f"Echo server activo en {st.session_state.echo_server['base_url']}")
        else:
            st.info("Echo server no disponible.")
        if _el_serve and "el_server" in st.session_state:
            st.success(f"ElevenLabs sim activo en {st.session_state.el_server['base_url']}")
        else:
            st.info("ElevenLabs server no disponible.")
    with col_b:
        st.markdown("### Ciclo Rápido (Subprocess)")
        run_demo = st.button("Ejecutar Router Demo")
        if run_demo:
            backend_root = Path(__file__).resolve().parents[1] / "backend"
            router_py = backend_root / "src" / "agents" / "router.py"
            if router_py.exists():
                args = [sys.executable, str(router_py), "--payload", json.dumps({"type": "ping", "from": "ui"})]
                res = _run_subprocess(args)
                if res["success"]:
                    st.code(res.get("stdout") or "", language="json")
                else:
                    st.error("Fallo en subprocess")
                    st.code(res.get("stderr") or res.get("stdout") or "", language="text")
            else:
                st.warning("router.py no encontrado.")

    if store:
        pid = st.session_state.get("patient_id", "demo_patient") or "demo_patient"
        sess = store.get(pid)
        with st.expander("Exportar Sesión JSON"):
            exported = store.export_json(sess.patient_id)
            encrypt_opt = st.checkbox("Cifrar exportación (Fernet)", value=False, help="Requiere dependencia 'cryptography'.")
            password = ""
            encrypted_payload = None
            if encrypt_opt:
                password = st.text_input("Contraseña", type="password", help="Mínimo 10 caracteres, incluir letra y dígito.")

                def _password_policy(pw: str) -> tuple[bool, str]:
                    if len(pw) < 10:
                        return False, "Debe tener al menos 10 caracteres."
                    if not re.search(r"[A-Za-z]", pw):
                        return False, "Debe incluir al menos una letra."
                    if not re.search(r"[0-9]", pw):
                        return False, "Debe incluir al menos un dígito."
                    return True, "OK"

                if password:
                    ok, reason = _password_policy(password)
                    if ok:
                        st.success("Contraseña válida.")
                        if st.button("Generar Exportación Cifrada"):
                            try:
                                from backend.src.utils.encryption import encrypt_json  # type: ignore
                                encrypted_payload = encrypt_json(exported, password)
                                st.session_state.last_encrypted_export = encrypted_payload
                                st.success("Exportación cifrada lista.")
                            except RuntimeError:  # noqa: BLE001
                                st.error("Cifrado no disponible (instala 'cryptography').")
                            except Exception as e:  # noqa: BLE001
                                st.error(f"Error al cifrar: {e}")
                    else:
                        st.warning(f"Contraseña débil: {reason}")
                        # Botón deshabilitado visualmente (placeholder) si política no cumple
                        st.button("Generar Exportación Cifrada", disabled=True)
                payload = st.session_state.get("last_encrypted_export")
                if isinstance(payload, str) and payload:
                    st.download_button(
                        "Descargar Cifrado", data=payload.encode("utf-8"), file_name=f"{sess.patient_id}_session.enc.json", mime="application/json"
                    )
                    st.caption("Guarda la contraseña de forma segura; no se almacena.")
            if not encrypt_opt:
                st.download_button(
                    "Descargar", data=exported.encode("utf-8"), file_name=f"{sess.patient_id}_session.json", mime="application/json"
                )
    else:
        st.caption("Persistencia no inicializada; no hay export.")

st.markdown("</div>", unsafe_allow_html=True)