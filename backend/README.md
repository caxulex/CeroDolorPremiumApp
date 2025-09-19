Backend utilities

Agent CLIs
- AIP: `python src/agents/aip.py --ping`
- ASD: `python src/agents/asd.py --ping`
- AIPer: `python src/agents/aiper.py --ping`

Router demo
- Chain AIP -> ASD -> AIPer locally (no external APIs unless keys are set):
  - `python src/agents/router.py`
  - Or use PowerShell helper: `./scripts/run_backend_demo.ps1` from repo root
  - To pass a custom payload on PowerShell, prefer a file:
    - `python src/agents/router.py --payload-file backend/samples/router_payload.custom.json`
    - Or: `./scripts/run_router_with_payload.ps1`
 - MCP Mode (uses client shim; requires running server endpoints):
   - `python src/agents/router.py --mcp --mcp-base-url http://localhost:3000 --mcp-send`

Environment
- `ELEVENLABS_API_KEY` enables optional TTS/STT helpers
- `MISTRAL_API_KEY` enables optional analysis/suggestions

Mock MCP server
- Emulates an MCP-like transport with simple envelopes and correlation IDs
  - Run: `./scripts/run_mock_mcp.ps1`
  - Output: `backend/mock_mcp.output.json`

MCP client shim (minimal)
- Validates our contract and optionally sends to a running server/inspector
  - Probe health:
    - `pwsh -File scripts/run_mcp_client.ps1` (defaults to `http://localhost:3000/health`)
  - Dry-run mapping only:
    - `C:\\Users\\caxul\\CeroDolorPreminumApp\\.venv\\Scripts\\python.exe backend/src/mcp/client.py --payload '{"pain_level":7}'`
  - POST mapped payload (adjust endpoints):
    - `pwsh -File scripts/run_mcp_client.ps1 -EchoPath "/echo" -PayloadFile backend/samples/router_payload.custom.json -Send`

SSE MCP client (Coral)
- Connects to Coral's MCP server via SSE and prints incoming events as JSON.
  - First event only (with timeout):
    - `& ..\\.venv\\Scripts\\python.exe backend\\src\\mcp\\sse_client.py --url http://localhost:5555 --path / --once --timeout 10`
  - Continuous stream:
    - `& ..\\.venv\\Scripts\\python.exe backend\\src\\mcp\\sse_client.py --url http://localhost:5555 --path /`
  - Smoke wrapper (from repo root):
    - `& ..\\.venv\\Scripts\\python.exe scripts\\mcp_client_smoke.py --url http://localhost:5555 --path / --once`
  - Notes:
    - If your server exposes SSE at another path, pass `--path /sse`.
    - Use `--token <BEARER>` if Coral requires an auth header.

Coral MCP (Scaffold)
- Helper scripts to prepare local Coral MCP repos without affecting tests/CI
  1) Clone repos (uses defaults if no URLs provided):
    - `pwsh -File scripts/setup_coral_repos.ps1`
    - Defaults: servers, inspector, and lastmile-ai/mcp-agent cloned under `external/`
    - Or override with your forks/branches via URL params
  2) Install dependencies:
    - `pwsh -File scripts/setup_coral_repos.ps1 -Install -NodePm npm -Python "C:\\Path\\to\\python.exe"`
  3) Run services and agents (use the actual start commands for your repos):
    - `pwsh -File scripts/run_coral_services.ps1 -ServerDir .\\external\\coral-server -ServerStartCmd "npm run start" -StudioDir .\\external\\coral-studio -StudioStartCmd "npm run dev" -AgentsDir .\\external\\coral-agents-examples -AgentsStartCmd @("python agent_aip.py","python agent_asd.py","python agent_aiper.py")`
  4) Probe ping-pong (replace with your actual client command):
    - `pwsh -File scripts/probe_coral_pingpong.ps1 -ProbeCommand "curl http://localhost:PORT/health"`

Tip: Copy `scripts/coral.services.config.example.ps1` to `coral.services.config.ps1` and customize paths/commands, then call `run_coral_services.ps1` with those variables.

Adapters & Offline Mode
-----------------------

This repo includes adapter shims for third-party APIs with an offline-first approach. By default, adapters simulate deterministic outputs so tests and demos remain stable with no network.

- Env flags
  - `USE_ADAPTERS=true`: Route service calls through adapters (offline by default).
  - `USE_NETWORK=true`: Allow adapters to attempt real HTTP calls (only if the corresponding API key is set).
  - `ELEVENLABS_API_KEY`: Unlocks optional TTS/STT (AIP service) when using adapters or direct SDK.
  - `MISTRAL_API_KEY`: Unlocks optional analysis/suggestions (ASD/AIPer services) when using adapters or direct SDK.

- Services wired to adapters (behind `USE_ADAPTERS=true`)
  - AIP (`backend/src/services/aip_service.py`):
    - TTS: Uses `integrations.ElevenLabsClient.synthesize()`; offline returns stub audio metadata encoded as bytes.
    - STT: Uses `integrations.ElevenLabsClient.transcribe()`; offline returns a stable Spanish transcript.
  - ASD (`backend/src/services/asd_service.py`):
    - Analysis: Uses `integrations.MistralClient.extract()`; offline returns a fixed structure mapped into the service schema.
  - AIPer (`backend/src/services/aiper_service.py`):
    - Suggestion: Uses `integrations.MistralClient.chat()`; offline returns a deterministic assistant message.

- Run adapter-backed flows offline (PowerShell)
  1) Activate the venv:
     - `& ..\.venv\Scripts\Activate.ps1` (from repo root)
  2) Set flags to force offline adapters (no network/keys required):
     - `$env:USE_ADAPTERS = 'true'`
     - `$env:USE_NETWORK = 'false'`
     - `Remove-Item Env:\ELEVENLABS_API_KEY -ErrorAction SilentlyContinue`
     - `Remove-Item Env:\MISTRAL_API_KEY -ErrorAction SilentlyContinue`
  3) Run unit tests and demos:
     - `..\.venv\Scripts\python.exe -m pytest -q`
     - `..\.venv\Scripts\python.exe backend/src/agents/router.py`

- Real HTTP integrations (optional, future)
  - Implement the HTTP calls inside `backend/src/integrations/elevenlabs.py` and `mistral.py` when ready (using `requests`).
  - Adapters already gate calls on `USE_NETWORK=true` and the matching API key; keep offline paths intact for CI stability.
  - Add integration tests guarded by env vars so CI stays network-free, e.g.:
    - Skip unless `$env:USE_NETWORK -eq 'true'` and the API key is present.
    - Probe against a mock server or a small quota endpoint; assert structure only.
  - Document any additional env vars (custom base URLs, model/voice IDs) in this section.

Clinician Report (AIC)
----------------------

We provide a minimal clinician weekly report generator that produces a structured, schema-validated payload (offline-first).

- Schema: `specs/001-description-esta-secci/contracts/clinician_report.json`
- Service: `backend/src/services/aic_service.py` → `generate_structured_report(patient_id, data=None)`
- CLI: `python src/agents/aic_cli.py <patient_id> [--data path/to/input.json] [--out report.json]`

Example (PowerShell):

1) Activate venv and ensure offline mode (no network required):
  - `& ..\.venv\Scripts\Activate.ps1`
  - `$env:USE_ADAPTERS = 'true'`  # optional: let AIC try ASD analysis if available
  - `$env:USE_NETWORK = 'false'`

2) Generate report to stdout:
  - `..\.venv\Scripts\python.exe backend/src/agents/aic_cli.py patient-123`

3) Or write to file and then validate in tests:
  - `..\.venv\Scripts\python.exe backend/src/agents/aic_cli.py patient-123 --out backend/samples/clinician_report.patient-123.json`

Proyecto B: Red de Cuidado Descentralizada
------------------------------------------

Contratos y flujo offline-first para AI↔AP con billetera de datos y micropagos simulados.

- Esquemas: ver `specs/001-description-esta-secci/contracts/` (research_query, data_offer, anonymized_data_bundle, micropayment_receipt, audit_log_entry)
- Servicio: `backend/src/services/research_network_service.py`
- CLIs:
  - AP: `python backend/src/agents/patient_agent.py --patient-id p1 --profile backend/samples/patient.profile.json --query backend/samples/research.query.json --data backend/samples/patient.data.json`
  - AI: `python backend/src/agents/investigator_agent.py --query backend/samples/research.query.json`
  - AC: `python backend/src/agents/clinician_agent.py --request backend/samples/clinician.request.json`

Notas
- `USE_ADAPTERS=true` habilita Crossmint/Solana offline; `USE_NETWORK=true` intentará llamadas reales si configuras claves/URLs.

Recuperación rápida
-------------------
Consulta `RECOVERY.md` en la raíz del repositorio para ver cómo volver rápidamente al checkpoint.

Crossmint & Solana (Network Mode)
---------------------------------

Por defecto, los adapters corren en modo offline para estabilidad en CI. Para activar rutas de red:

- Requisitos de entorno:
  - `USE_NETWORK=true`
  - Crossmint: `CROSSMINT_API_KEY`, opcional `CROSSMINT_BASE_URL`, `CROSSMINT_COLLECTION_ID`
  - Solana: `SOLANA_RPC_URL` (p. ej., https://api.devnet.solana.com), opcional `SOLANA_PAYER_SECRET`

Ejemplo (PowerShell):

```powershell
& ..\.venv\Scripts\Activate.ps1
$env:USE_NETWORK = 'true'
$env:SOLANA_RPC_URL = 'https://api.devnet.solana.com'
$env:SOLANA_PAYER_SECRET = 'dev-only-secret'
# Opcional Crossmint
# $env:CROSSMINT_API_KEY = '<tu_key>'

# Ejecutar solo pruebas de red (se omiten si faltan variables)
..\.venv\Scripts\python.exe -m pytest -q tests\integration\test_integrations_network.py
```

Notas:
- El adapter de Solana retorna una firma dummy (HMAC) en modo red y no transmite la transacción.
- Mantén `USE_NETWORK=false` en CI para evitar flakiness.

Streamlit UI & Persistencia Ligera
----------------------------------

La interfaz `frontend/app.py` provee:
- Chequeo diario (AIP service) con registro de dolor, estado de ánimo y sueño.
- Demos del router (local, MCP, MAS) con visualización de validaciones y reporte clínico (AIC) opcional.
- Botón para ejecutar flujo MAS (Paciente→Clínico→Fisio) y mostrar transcript MCP si se habilita.
- Persistencia liviana: cada evento se guarda bajo `backend/sessions/<patient>.json` mediante `SessionStore` (`backend/src/utils/persistence.py`).

Estructura de sesión:
```jsonc
{
  "patient_id": "demo_patient",
  "events": [
    {"id": 1, "ts": "2025-09-16T18:20:00Z", "type": "start_checkin", "data": {"message": "..."}},
    {"id": 2, "ts": "...", "type": "pain_registration", "data": {"pain": {"level":5}}}
  ],
  "meta": {"created_ts": "...", "updated_ts": "..."}
}
```

Exportar: dentro del panel "Historial Persistente de Sesión" pulsa "Descargar Sesión JSON".

Ejecutar UI (PowerShell desde la raíz):
```powershell
& .\.venv\Scripts\Activate.ps1
..\.venv\Scripts\python.exe -m streamlit run frontend/app.py
```

Notas técnicas:
- Escritura atómica usando archivo temporal `*.tmp` y `Path.replace()`.
- Limpia caracteres no permitidos en el nombre de archivo de sesión.
- No bloquea si la persistencia falla (UI sigue funcionando en memoria).

Tabs & Funcionalidades (Actualizado)
-----------------------------------
- Chequeo Diario: Registro de dolor/animo/sueño y feedback; guarda eventos.
- MAS: Ejecuta flujo MAS con validaciones, tiempos de construcción (`timings_ms`), AIC opcional, transcript MCP (si habilitado) y timeline.
- Router: Ejecución directa de la cadena AIP→ASD→AIPer (con AIC opcional) y modo MCP separado; muestra badges de validación.
- Audio: Simulación TTS/STT (adapters/ElevenLabs); descarga de bytes simulados; transcripción simulada.
- Config: Diagnóstico de entorno y presencia de claves.
- Historial: Eventos persistidos + descarga JSON + log efímero.

Badges de Validación
Cada contrato muestra: OK (verde), ERR (rojo) o NA (gris). En caso de error se incluye el primer mensaje.

Rendimiento
Se listan duraciones de construcción de mensajes MAS y duración de generación AIC. Si MCP activo, se muestran duraciones por hop.

Extender a Modo Real (Opcional)
Para habilitar integraciones reales (cuando se implementen llamadas HTTP):
```powershell
$env:USE_ADAPTERS='true'
$env:USE_NETWORK='true'
$env:ELEVENLABS_API_KEY='xxxxx'
$env:MISTRAL_API_KEY='yyyyy'
```
Mantén en CI: `USE_NETWORK=false`.

Analítica de Dolor (Pain Trends)
--------------------------------
La UI ahora calcula métricas ligeras tras cada registro de dolor usando `compute_pain_stats` (`backend/src/utils/analytics.py`):

- `last`: último nivel de dolor
- `mean_last_3` / `mean_last_7`: medias móviles (hasta 3 / 7 valores)
- `delta_last`: diferencia vs el valor inmediatamente anterior
- `pct_change_last`: cambio porcentual (omitido si división por cero)
- `zscore_last`: z-score del último valor (si varianza suficiente)
- `anomaly`: True si |z| ≥ 2 o salto absoluto ≥ 4 puntos
- `severity_trend`: "up" / "down" / "flat" según los últimos 3 puntos

Edge cases manejados:
- Lista vacía: todos los campos None excepto `count=0`.
- Un solo valor: sin delta ni z-score; anomaly=False.
- Valores constantes: stdev ~ 0 → z-score None.

Visualización:
- Métricas clave (Último, medias móviles, delta, % cambio, anomalía) en Chequeo Diario tras registrar.
- Resumen completo en la pestaña Historial.

Correlaciones y Agregados Semanales
-----------------------------------
Funciones adicionales en `backend/src/utils/analytics.py`:
- `compute_correlations(events)`: correlación (Pearson) exploratoria entre dolor↔ánimo y dolor↔sueño tras mapear categorías a escalas ordinales.
- `weekly_aggregate(events)`: agrupa `pain_registration` por semana ISO (`YYYY-Www`) con métricas: `count`, `avg`, `min`, `max`.

Notas:
- Correlaciones requieren ≥ 3 puntos de dolor; de lo contrario devuelven `None`.
- Mapas heurísticos (ej.: ánimo "feliz"→5, "deprimido"→0) — no clínicamente validados.
- Agrupación semanal tolera timestamps con sufijo `Z` o offsets.

Analítica Avanzada (Extensiones Nuevas)
--------------------------------------
Funciones añadidas:
- `bootstrap_correlation_ci(xs, ys, n_boot=500)`: intervalo de confianza bootstrap (percentil) para r de Pearson; determinista con `seed`.
- `weekly_trends(weekly)`: añade `delta_vs_prev` a cada semana para evaluar cambio relativo.
- `cross_feature_anomalies(events)`: detecta patrones compuestos (dolor >=8 + mal sueño/ánimo negativo, o salto súbito >=4 con contexto).
- `build_analytics_snapshot(events)`: genera snapshot consolidado (`pain`, `weekly` + deltas, `correlations`, `correlation_ci`, `anomalies`).

Persistencia de Snapshots:
- Cada envío de dolor en la UI dispara `analytics_snapshot` (evento) para histórico longitudinal.
- Historial muestra última foto + tabla semanal + correlaciones (con CI si disponible) + anomalías recientes.

Heurísticas & Límites:
- Correlaciones categóricas dependen de mapas ordinales heurísticos (no diagnóstico clínico).
- Bootstrap CI: simple remuestreo; no bias correction.
- Anomalías compuestas: reglas definidas manualmente; sugerido evolucionar a scoring probabilístico.

Ideas Futuras:
- Normalizar por hora del día o fase de medicación.
- Detección de tendencia usando regresión robusta (Theil-Sen) en vez de delta simple.
- Persistir snapshots agregados (mensual) para reducir tamaño de sesión.

Timeline Estilizado
-------------------
El transcript MCP/MAS se representa con un componente vertical (CSS en `frontend/styles/empathy-agent.css`):

- Línea vertical + nodos circulares para cada hop (`patient`, `clinician`, `physio`, `aic_report`).
- Badges OK/ERR/NA indican validación de cada bloque.
- Duración por hop en ms para diagnóstico de latencia.
- `data-reveal` atributos preparados para efectos de aparición progresiva (opt-in futuro JS si se necesitara).

Extensión futura sugerida:
- Tooltips con payload resumido.
- Filtros para mostrar/ocultar tipos de hop.
- Comparativa de latencias promedio vs. actual (requiere almacenamiento histórico agregado).

Pruebas de Analítica
--------------------
Archivo: `tests/unit/test_analytics.py`
Cubre: vacío, valor único, tendencia ascendente, salto (anomalía), z-score outlier y cálculo de % cambio.

Notas de Integración HTTP Real
------------------------------
Se implementaron llamadas HTTP básicas (gated) en:
- `backend/src/integrations/elevenlabs.py`: `/v1/transcriptions`, `/v1/text-to-speech/{voice}`
- `backend/src/integrations/mistral.py`: `/v1/chat/completions`

Condiciones para ejecutar llamadas reales:
- `USE_NETWORK=true` y API key correspondiente presente.
- Se mantienen rutas simuladas determinísticas para estabilidad.

Estrategia de testing recomendada (no incluida aún):
- Tests de integración marcados con `@pytest.mark.network` que se saltan si `USE_NETWORK != 'true'`.
- Asserts limitados a forma (shape) y claves obligatorias, no contenido textual exacto.

Avances Recientes (Resumen Rápido)
----------------------------------
- Integraciones HTTP reales (gated) para ElevenLabs (TTS/STT) y Mistral (chat/extract) manteniendo rutas simuladas deterministas.
- Analítica de dolor ligera con medias móviles, deltas, z-score y detección de anomalías (salto o outlier estadístico) integrada en la UI.
- Timeline estilizado con estados visuales y badges de anomalía opcional.
- Persistencia por paciente con exportación JSON atómica.

Detalles de Analítica (Implementación)
-------------------------------------
Archivo: `backend/src/utils/analytics.py`

Reglas de anomalía:
- `|zscore_last| >= 2` (si varianza suficiente y n ≥ 2)
- `abs(delta_last) >= 4` (salto abrupto)

Wrapper de sesión: `integrate_session_events(events)` extrae niveles desde eventos `pain_registration`.

UI Rendering:
- Chequeo Diario: métricas clave + badge de anomalía si aplica.
- Historial: resumen completo con badge "Anomalía Detectada".

Timeline Avanzado
-----------------
CSS: `frontend/styles/empathy-agent.css` emplea clases semánticas:
- `.cd-t-item.ok|err|na` para colorear borde/fondo.
- `.cd-badge.anomaly` para resaltar un estado de anomalía.

Extensiones Futuras (Ideas)
---------------------------
- Correlación dolor ↔ sueño/ánimo.
- Latencia promedio histórica vs. actual en timeline.
- Exportación CSV de métricas agregadas.
- Badges de severidad (leve/moderado/severo) calculados dinámicamente.

<!-- MANUAL ADDITIONS START -->
Caching de Snapshots Analíticos
--------------------------------
Para reducir recomputo de `build_analytics_snapshot` se introdujo `compute_or_get_snapshot` (`backend/src/utils/snapshot_cache.py`).
La función calcula un hash compacto de eventos (id, type, pain_level) y devuelve `_cache_hit=True` si no hubo cambios. Solo se persiste un nuevo evento `analytics_snapshot` cuando el hash difiere.

Accesibilidad (A11y)
--------------------
- Timeline ahora usa `role=list` y cada item `role=listitem`.
- Sparkline y escala de dolor usan `role=img` + `aria-label` descriptivo.
- Prueba de contraste WCAG AA en `tests/accessibility/test_contrast.py` valida pares críticos (texto primario, badges, acento).

E2E (Playwright) Scaffold
-------------------------
Archivo: `tests/e2e/test_daily_checkin_e2e.py` marcado `@pytest.mark.e2e`. Se omite si Playwright no está instalado.

Para habilitar:
```powershell
pip install playwright
playwright install
pytest -m e2e -q
```

Roadmap A11y futuro:
- Navegación full teclado verificada.
- Labels asociados a todos los inputs vía `aria-labelledby` o `for` en renderizado custom (Streamlit limita parte de esto).
- Modo alto contraste alternativo.
\n+Orquestador de Agentes Unificado
---------------------------------
Archivo: `backend/src/agents/orchestrator.py` expone `run_patient_cycle(...)` que encadena AIP → ASD → AIPer → (AIC opcional) y persiste:
- `pain_registration`, `mood_sleep`, `insights`, `suggestion`, `clinician_report` (si incluye), `orchestrated_cycle`.

Ventajas clave:
- Reutiliza servicios existentes (offline determinista / adapters reales según flags).
- Minimiza acoplamiento UI ↔ servicios individuales (una sola llamada).
- Facilita testing (`tests/unit/test_orchestrator_cycle.py`).

Scheduler Semanal de Reportes
-----------------------------
Archivo: `backend/src/agents/scheduler.py` con:
- `needs_weekly_report(patient_id)` → bool si han pasado ≥7 días o no hay reporte.
- `maybe_generate_weekly_report(patient_id)` → genera y persiste reporte con `auto: true` si corresponde.

Integración UI:
- Nueva pestaña "Agentes" permite ejecutar un ciclo y gatillar reporte semanal si está vencido.
- Botón contextual "Generar reporte semanal (auto)" visible sólo cuando `needs_weekly_report` es True.

Eventos Nuevos:
- `orchestrated_cycle`: snapshot integral del output multi-agente.
- `clinician_report` (con campo `auto` cuando proviene del scheduler).

Ejemplo simplificado de ciclo:
```jsonc
{
  "patient_id": "demo_patient",
  "aip": {"pain": {"level": 6, "description": "lumbar"}},
  "asd": {"patterns_detected": ["placeholder"], "trend_analysis": "stable"},
  "aiper": {"suggestion": "Try a 5-minute guided breathing exercise."},
  "aic": {"report": {"period": "last_7_days", "patterns_detected": []}}
}
```

Siguientes mejoras sugeridas:
- Enriquecer AIP con mini-historial contextual en cada ciclo.
- AIPer selecciona intervención basada en patrones específicos (mapa pattern→plantilla).
- AIC agrega KPIs de adherencia calculados desde eventos (porcentaje de días con check-in).
- Métricas de latencia por agente en `orchestrated_cycle` para observar performance.
\n+Proyecto B: Arquitectura de Red Descentralizada (Añadido)
---------------------------------------------------------
Componentes nuevos:
- `consent_service.py`: gestiona concesión / revocación (eventos `consent_grant` / `consent_revoke`).
- `anonymization_service.py`: hash determinista + filtrado de campos.
- `network_orchestrator.py`: coordina flujos AP⇄AC (solicitudes clínicas) y AP⇄AI (difusión de queries de investigación).
- Extensión `research_network_service.py`: ahora exige consent por campo y persiste eventos `research_offer`, `research_bundle`, `research_receipt`, `research_denied`.

Nuevos eventos (SessionStore):
- `consent_grant`, `consent_revoke`
- `clinician_request`
- `research_query_received`, `research_fulfill_error`, `research_fulfilled`, `research_denied`
- `research_offer`, `research_bundle`, `research_receipt`

Pestaña UI "Red":
- Wallet: crear/derivar (simulado) dirección paciente.
- Permisos: dashboard de consentimientos granulares por tipo de dato.
- Solicitudes Clínico: registrar petición y conceder/revocar en lote.
- Investigación: pegar/modificar query y ejecutar broadcast; respeta consentimientos.
- Auditoría: lectura tail de `backend/audit/project_b.jsonl`.

Flujo Clínico (AC):
1. AC envía solicitud (`clinician_request`).
2. Paciente concede (uno o varios data types) → `consent_grant`.
3. Revocación posterior opcional → `consent_revoke`.

Flujo Investigación (AI):
1. AI difunde `research_query`.
2. AP evalúa criterios (`evaluate_query_against_patient`).
3. Si match, verifica consent por cada campo requerido.
4. Si falta consent → `research_denied`.
5. Si todo ok: mint + hash + receipt (offline) y eventos `research_offer` → `research_bundle` → `research_receipt` + `research_fulfilled`.

Anonymización:
- Hash SHA-256 de subconjunto filtrado; estable y sin datos reversibles.
- Tests aseguran estabilidad de hash ante cambio de orden de claves.

Tests Añadidos:
- `test_project_b_consent_and_research.py`: ciclo de consent, enforcement de campos, hash estable.

Mejoras Futuras (Roadmap B):
- Políticas de consentimiento por duración / expiración.
- Estrategia de anonimización configurable (enmascarar, bucketizar, k-anonymity heurística).
- Simulación de micro-lote de pacientes para stress-test de matching.
- Firma criptográfica local de recibos antes de persistir.
- Exportación de auditoría filtrada por requester.

Servidor MCP ElevenLabs (Local)
--------------------------------
Archivo: `backend/src/mcp/elevenlabs_server.py`

Endpoints:
- `GET /health` → estado y flags
- `GET /voices` → voces demo (estático)
- `POST /echo`  → eco JSON
- `POST /tts`   → sintetiza (usa `tts_generate_bytes` si disponible; fallback pseudo bytes base64)
- `POST /stt`   → placeholder transcripción (texto fijo)

Auto-arranque UI:
La UI levanta el servidor en un puerto dinámico y expone `st.session_state.el_server.base_url`.

Ejemplo manual (PowerShell):
```powershell
& ..\.venv\Scripts\Activate.ps1
..\.venv\Scripts\python.exe -m backend.src.mcp.elevenlabs_server --port 3031
curl http://127.0.0.1:3031/health
curl -X POST http://127.0.0.1:3031/tts -H "Content-Type: application/json" -d '{"text":"hola","voice":"demo_female"}'
```

Integración como MCP en plataformas externas:
1. Seleccionar tipo servidor HTTP reproducible.
2. Base URL: `http://127.0.0.1:<puerto>`.
3. Declarar herramientas `tts`, `echo`, `voices` (y `stt` opcional) según soporte.

Evolución futura:
- Streaming chunked / SSE para audio.
- Endpoint real STT con modelo local.
- Cache de voces dinámico.
- Firma HMAC del payload de salida para reproducibilidad.

<!-- MANUAL ADDITIONS END -->

