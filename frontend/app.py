import streamlit as st
import json
import subprocess
import sys
from pathlib import Path

# Optional: local echo server for MCP demo
try:
    from backend.src.mcp.echo_server import serve_in_thread as _echo_serve
except Exception:  # pragma: no cover - UI fallback
    _echo_serve = None

st.set_page_config(page_title="CeroDolor - Chequeo Diario", page_icon="🩺")

st.title("Agente de Empatía Crónica")

# Start a local echo server (once) for MCP demo if available
if _echo_serve and "echo_server" not in st.session_state:
    httpd, thread, bound_port = _echo_serve(0)
    st.session_state.echo_server = {
        "httpd": httpd,
        "thread": thread,
        "port": bound_port,
        "base_url": f"http://127.0.0.1:{bound_port}",
    }

if "log" not in st.session_state:
    st.session_state.log = []

patient_id = st.text_input("ID del paciente", value="demo_patient")

col1, col2 = st.columns(2)
with col1:
    start = st.button("Iniciar Chequeo Diario")
with col2:
    submit = st.button("Enviar Registro de Dolor")

if start:
    from backend.src.services.aip_service import initiate_daily_checkin
    msg = initiate_daily_checkin(patient_id)
    st.session_state.log.append(msg)

pain_level = st.slider("Nivel de dolor (1-10)", 1, 10, 5)
pain_desc = st.text_input("Descripción del dolor", "punzante en la espalda baja")
mood = st.text_input("Estado de ánimo", "ansioso")
sleep = st.text_input("Calidad del sueño", "mal")

if submit:
    from backend.src.services.aip_service import register_pain, register_mood_sleep, provide_feedback
    from backend.src.services.asd_service import analyze_data
    from backend.src.services.aiper_service import generate_intervention

    pain = register_pain(patient_id, pain_level, pain_desc)
    ms = register_mood_sleep(patient_id, mood, sleep)
    st.session_state.log.append(f"Registro: {pain} | {ms}")

    insights = analyze_data(patient_id, {"pain": pain, "mood_sleep": ms})
    st.session_state.log.append(f"Insights: {insights}")

    suggestion = generate_intervention(patient_id)
    st.success(f"Sugerencia: {suggestion}")

    feedback = provide_feedback(patient_id, "post-registro")
    st.info(feedback)

st.subheader("Actividad")
for line in st.session_state.log:
    st.write("• ", line)

st.divider()
st.header("Demos backend")

backend_root = Path(__file__).resolve().parents[1] / "backend"
python_bin = Path(sys.executable)
router_py = backend_root / "src" / "agents" / "router.py"
mock_mcp_py = backend_root / "src" / "mcp" / "mock_server.py"
mcp_router_hint = "Ejecuta el router en modo MCP (requiere servidor/inspector corriendo)"

with st.expander("Router AIP → ASD → AIPer"):
    default_payload = {
        "type": "ping",
        "from": "ui",
    }
    payload_text = st.text_area(
        "Payload JSON inicial",
        value=json.dumps(default_payload, ensure_ascii=False, indent=2),
        height=120,
    )
    include_aic = st.checkbox("Incluir reporte clínico (AIC)", value=False)
    if st.button("Ejecutar Router"):
        try:
            payload = json.loads(payload_text)
        except json.JSONDecodeError as e:
            st.error(f"JSON inválido: {e}")
        else:
            try:
                args = [str(python_bin), str(router_py), "--payload", json.dumps(payload)]
                if include_aic:
                    args.append("--include-aic")
                proc = subprocess.run(
                    args,
                    capture_output=True,
                    text=True,
                    check=True,
                )
                st.code(proc.stdout, language="json")
                try:
                    data = json.loads(proc.stdout)
                except json.JSONDecodeError:
                    data = {}
                if isinstance(data, dict) and data.get("aic_report"):
                    st.subheader("Reporte Clínico (AIC)")
                    st.code(json.dumps(data["aic_report"], ensure_ascii=False, indent=2), language="json")
            except subprocess.CalledProcessError as e:
                st.error("Fallo ejecutando router")
                st.code(e.stderr or e.stdout, language="text")

with st.expander("Router (Modo MCP)"):
    st.caption(mcp_router_hint)
    default_base = (
        st.session_state.echo_server["base_url"]
        if "echo_server" in st.session_state
        else "http://localhost:3000"
    )
    base_url = st.text_input("MCP Base URL", value=default_base)
    echo_path = st.text_input("Echo path", value="/echo")
    health_path = st.text_input("Health path", value="/health")
    st.caption(f"Usando: base={base_url} echo={echo_path} health={health_path}")
    payload_text_mcp = st.text_area(
        "Payload JSON inicial",
        value=json.dumps({"type": "ping", "from": "ui-mcp"}, ensure_ascii=False, indent=2),
        height=120,
    )
    do_send = st.checkbox("Enviar (POST) al servidor", value=False)
    if st.button("Ejecutar Router (MCP)"):
        try:
            payload = json.loads(payload_text_mcp)
        except json.JSONDecodeError as e:
            st.error(f"JSON inválido: {e}")
        else:
            try:
                args = [
                    str(python_bin),
                    str(router_py),
                    "--payload",
                    json.dumps(payload),
                    "--mcp",
                    "--mcp-base-url",
                    base_url,
                    "--mcp-echo-path",
                    echo_path,
                    "--mcp-health-path",
                    health_path,
                ]
                if do_send:
                    args.append("--mcp-send")
                proc = subprocess.run(args, capture_output=True, text=True, check=True)
                st.code(proc.stdout, language="json")
                # Attempt to render basic MCP metadata
                try:
                    data = json.loads(proc.stdout)
                    m = data.get("mcp", {}) if isinstance(data, dict) else {}
                    if m:
                        st.subheader("MCP Resumen")
                        if isinstance(m, dict):
                            if m.get("id"):
                                st.write(f"ID: {m['id']}")
                            if m.get("ts"):
                                st.write(f"TS: {m['ts']}")
                            if m.get("duration_ms"):
                                st.write(f"Duración: {m['duration_ms']} ms")
                            if "validation" in m:
                                st.caption(f"Validación: {json.dumps(m['validation'], ensure_ascii=False)}")
                except json.JSONDecodeError:
                    pass
            except subprocess.CalledProcessError as e:
                st.error("Fallo ejecutando router (MCP)")
                st.code(e.stderr or e.stdout, language="text")

with st.expander("Mock MCP (con sobres/envelopes)"):
    if st.button("Ejecutar Mock MCP"):
        try:
            proc = subprocess.run(
                [str(python_bin), str(mock_mcp_py)],
                capture_output=True,
                text=True,
                check=True,
            )
            # Show raw
            st.code(proc.stdout, language="json")
            # Parsed transcript viewer
            try:
                data = json.loads(proc.stdout)
            except json.JSONDecodeError:
                data = {}
            transcript = data.get("transcript", []) if isinstance(data, dict) else []
            if transcript:
                st.subheader("Transcript")
                for i, item in enumerate(transcript, start=1):
                    if "send" in item:
                        env = item["send"]
                        st.markdown(f"- Enviar #{i}: {env.get('source')} → {env.get('target')}")
                        if "validation" in item:
                            st.caption(f"Validación: {json.dumps(item['validation'], ensure_ascii=False)}")
                    elif "recv" in item:
                        rec = item["recv"]
                        st.markdown(f"  • Recv #{i} de {rec.get('from')}")
            else:
                st.info("No hay transcript para mostrar.")
        except subprocess.CalledProcessError as e:
            st.error("Fallo ejecutando mock MCP")
            st.code(e.stderr or e.stdout, language="text")

with st.expander("MAS Demo (Paciente → Clínico → Fisio)"):
    mas_payload = {
        "patient_id": patient_id or "demo_patient",
        "pain_level": pain_level,
        "pain_desc": pain_desc,
        "mood": mood,
        "sleep": sleep,
    }
    use_mcp = st.checkbox("Usar MCP (echo) para enviar mensajes", value=False)
    base_url = (
        st.session_state.echo_server["base_url"] if use_mcp and "echo_server" in st.session_state else "http://localhost:3000"
    )
    st.caption("Ejecuta un flujo mínimo de MAS con validación de contratos. Opcionalmente, envía cada mensaje al endpoint MCP (echo).")
    include_aic_mas = st.checkbox("Incluir reporte clínico (AIC)", value=True)
    if st.button("Ejecutar MAS Demo"):
        try:
            proc = subprocess.run(
                [
                    str(python_bin),
                    str(router_py),
                    "--mas-demo",
                    *( ["--mas-mcp"] if use_mcp else [] ),
                    *( ["--include-aic"] if include_aic_mas else [] ),
                    "--payload",
                    json.dumps(mas_payload, ensure_ascii=False),
                ],
                capture_output=True,
                text=True,
                check=True,
            )
            st.code(proc.stdout, language="json")
            try:
                data = json.loads(proc.stdout)
            except json.JSONDecodeError:
                data = {}
            if isinstance(data, dict):
                st.subheader("Validaciones")
                v = data.get("validation", {})
                if v:
                    st.write(v)
                st.subheader("Mensajes")
                for role in ("patient", "clinician", "physio"):
                    if role in data:
                        st.markdown(f"**{role.title()}**")
                        st.code(json.dumps(data[role], ensure_ascii=False, indent=2), language="json")
                if data.get("aic_report"):
                    st.subheader("Reporte Clínico (AIC)")
                    st.code(json.dumps(data["aic_report"], ensure_ascii=False, indent=2), language="json")
                if use_mcp and data.get("mcp_transcript"):
                    st.subheader("MCP Transcript")
                    for item in data["mcp_transcript"]:
                        lbl = item.get("label")
                        dur = item.get("duration_ms")
                        val = item.get("validation", {})
                        st.markdown(f"- {lbl} ({dur} ms)")
                        if val:
                            st.caption(f"Validación: {json.dumps(val, ensure_ascii=False)}")
                        st.code(json.dumps(item.get("post"), ensure_ascii=False, indent=2), language="json")
        except subprocess.CalledProcessError as e:
            st.error("Fallo ejecutando MAS Demo")
            st.code(e.stderr or e.stdout, language="text")