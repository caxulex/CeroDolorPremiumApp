# CeroDolor (Edición Producto Avanzada)

## Visión
CeroDolor es un asistente empático para personas con dolor crónico: capta información diaria (texto + voz), formula preguntas inteligentes, analiza patrones y sugiere micro‑intervenciones personalizadas. Todo comienza offline y escala a integraciones reales (ElevenLabs, Mistral) sólo si hay claves y banderas activadas.

## Flujo de Usuario (Actual)
1. Capturas tu estado: texto + (opcional) voz en vivo o clip.
2. Se resume automáticamente la transcripción (extracción heurística de localización, desencadenantes, ánimo, sueño).
3. Un motor de Guía Adaptativa formula la siguiente pregunta más informativa (según anomalías, tendencia, ánimo, sueño, localización, adherencia, mejora).
4. Se orquesta el ciclo multi‑agente (AIP → ASD → AIPer → AIC opcional) y se genera una intervención multi‑modal.
5. Recibes respuesta + audio WAV (fallback determinista si no hay TTS real) + badge del tipo de intervención.
6. Progreso muestra tendencias, correlaciones exploratorias y CIs bootstrap (dolor vs ánimo/sueño).
7. Avanzado permite exportar sesión en claro o cifrada (Fernet) y revisar analítica enriquecida.

## Características Clave
- **Resumen de Transcripción**: Extrae `location_keywords`, `triggers`, `aggravators`, `improvement`, `mood_hint`, `sleep_quality`.
- **Guía Adaptativa**: Selección heurística priorizada de categorías (`anomaly`, `trend`, `mood_sleep`, `location`, `trigger_followup`, `adherence`, `improvement`, `fallback`).
- **Intervenciones Multi‑Modal**: Tipos: `breathing`, `movement`, `mindfulness`, `education`, `reinforcement`, `mixed`, `llm_suggestion`, `general`.
- **Analítica Enriquecida**: Intervalos de confianza bootstrap de media de dolor y correlaciones dolor‑ánimo / dolor‑sueño.
- **Exportación Cifrada (Opcional)**: Fernet (PBKDF2 + SHA256) con contraseña provista por el usuario (no se persiste).
- **Chequeo Diario Unificado**: Registro de dolor, ánimo, sueño, voz, guías y sugerencia final.
- **Voz en Vivo (Beta)**: `streamlit-webrtc` (STT sim). Fallback WAV válido (RIFF/WAVE) determinista.
- **Persistencia Local**: JSON por paciente (`backend/sessions/<id>.json`).
- **Offline‑First**: Sin claves → heurísticas deterministas reproducibles.
- **Integraciones Escalonables**: Banderas `USE_ADAPTERS` / `USE_NETWORK` + keys.

## Arquitectura Resumida
| Capa | Descripción |
|------|-------------|
| UI (Streamlit) | 3 pestañas: Chequeo Diario, Progreso, Avanzado. Voz, guía, métricas y export. |
| Orchestrator | `run_patient_cycle` encadena servicios y persiste eventos. |
| Servicios | AIP (registro + TTS/STT), ASD (análisis), AIPer (intervención), AIC (reporte opcional). |
| Persistencia | `SessionStore` con escritura atómica y export JSON. |
| Integraciones | ElevenLabs (TTS/STT), Mistral (análisis/sugerencias), adaptadores offline. |
| Analítica | Cálculo rápido de stats + snapshot incremental (cacheable). |

### Contratos de Agentes
- Base compartida en `backend/src/agents/base.py` con `AgentRequest`, `AgentResponse` y `Agent` (Protocol).
- Los agentes deben exponer `ask(prompt) -> dict`, `reset()`, `health() -> dict`.
- `MistralAgent` soporta `timeout` y `retries`, e incluye `usage` si lo devuelve la API.

## Eventos Principales (SessionStore)
| Tipo | Descripción |
|------|-------------|
| `pain_registration` | Registro de nivel + descripción de dolor. |
| `mood_sleep` | Registro de ánimo y sueño. |
| `voice_transcript` | Texto bruto de transcripción de voz (snapshot incremental). |
| `transcript_summary` | Dict resumen heurístico (campos arriba). |
| `guided_dialogue` | Cada Q/A adaptativa individual. |
| `guided_dialogue_summary` | Resumen final de todas las respuestas guiadas del ciclo. |
| `intervention` | Intervención multi‑modal con `intervention_type` y `details`. |
| `insights` | Resultados ASD (patrones, flags). |
| `orchestrated_cycle` | Resultado completo del ciclo multi‑agente. |
| `clinician_report` | Reporte estructurado (si AIC activo). |
| (Futuro) `analytics_snapshot` | Snapshot consolidado periódico. |

## Modo Voz
| Modo | Fuente | Estado |
|------|--------|--------|
| Clip Subido | Archivo (uploader) | Estable |
| Voz en Vivo | WebRTC (micrófono) | Beta (STT sim) |
| STT Real | ElevenLabs / Adapter | Futuro (cuando se habilite USE_NETWORK) |

## Modo Conversacional (WebRTC + ElevenLabs)
Experiencia de conversación con captura de micrófono, transcripción automática y respuesta hablada.

Características
- Captura en vivo vía `streamlit-webrtc` (micrófono).
- Indicadores: estado de grabación, nivel RMS (barra), contador de segundos, clipping y “waveform” textual.
- STT parcial cada ~5s (feedback en vivo) y STT final al detener la grabación.
- Preferencias persistentes por paciente: `pref_voice`, `pref_autoplay`, `pref_el` (usar ElevenLabs), `pref_el_voice` (Voice ID opcional), `pref_privacy_no_wav` (no guardar WAV en disco).
- Botón “Probar voz” para validar TTS con ElevenLabs (o fallback local).
- Botón “Borrar transcripción de voz”.
- Persistencia de eventos: `voice_transcript_partial` (parciales), `voice_transcript` (final) y `voice_transcript_cleared` (borrado). Por defecto se guarda `backend/sessions/<paciente>_last.wav` para trazabilidad, salvo que actives el toggle de privacidad para no guardar WAV.

Activación rápida (PowerShell)
```powershell
# Offline determinista
$env:USE_NETWORK = "false"
$env:CERODOLOR_ENABLE_WEBRTC = "1"
python -m streamlit run frontend/app.py --server.port 8506

# ElevenLabs real (STT+TTS)
$env:USE_NETWORK = "true"
$env:ELEVENLABS_API_KEY = "<TU_API_KEY>"
# Opcional: voz concreta
$env:ELEVENLABS_TTS_VOICE_ID = "<VOICE_ID>"
python -m streamlit run frontend/app.py --server.port 8506
```

Notas de privacidad
- Con el modo conversacional activo, al finalizar una grabación se puede guardar el último WAV en `backend/sessions/<paciente>_last.wav` junto con eventos de transcripción. Si no deseas trazabilidad de audio, activa en Preferencias el toggle “No guardar archivos WAV de capturas en disco (privacidad)” para evitar la persistencia del archivo; alternativamente, desactiva WebRTC con `CERODOLOR_ENABLE_WEBRTC=0`.

Solución de problemas
- Si no aparece el botón START: instala `streamlit-webrtc` e intenta reiniciar la app.
	```powershell
	pip install streamlit-webrtc==0.47.1
	```
- Navegador sin permisos de micrófono: acepta permisos o usa otro navegador.
- STT/TTS real no funciona: asegúrate de `USE_NETWORK=true` y `ELEVENLABS_API_KEY` válidos.

## Agente Mistral (LLM opcional)
Puedes usar Mistral para generar sugerencias empáticas en vez del orquestador local.

- Variables de entorno:
	- `USE_NETWORK=true`
	- `MISTRAL_API_KEY=...`
	- Opcionales: `MISTRAL_MODEL` (por defecto `mistral-large-latest`), `MISTRAL_TEMPERATURE` (por defecto `0.4`).
- En la UI, en Preferencias, activa "Usar Mistral para sugerencias" y ajusta modelo/temperatura si lo deseas.
- Sin clave o con `USE_NETWORK=false`, el agente opera en modo simulado determinista.

Prueba rápida (offline determinista)
```powershell
pytest -q tests/test_mistral_agent.py
pytest -q tests/unit/test_mistral_extract_offline.py
```

Endpoint interno
- Cliente: `backend/src/integrations/mistral.py` (métodos `chat` y `extract`).
- Agente: `backend/src/agents/mistral_agent.py` (memoria ligera, system prompt, fallback determinista).

## Banderas de Entorno
```
USE_ADAPTERS=true|false   # Usa adaptadores deterministas
USE_NETWORK=true|false    # Permite HTTP real (si hay clave)
ELEVENLABS_API_KEY=...    # TTS/STT real (opcional)
ELEVENLABS_TTS_VOICE_ID=... # (Opcional) Voice ID por defecto para TTS
CERODOLOR_ENABLE_WEBRTC=1|0 # Habilitar/deshabilitar captura WebRTC (1 por defecto)
MISTRAL_API_KEY=...       # Análisis/Sugerencias reales
AIP_TTS_DIAG=true|false   # Envoltura diagnóstica en fallback TTS
```

## Ejecutar (Desarrollo)
```powershell
# 1. (Opcional) crear entorno
python -m venv .venv
& .\.venv\Scripts\Activate.ps1
pip install -r backend/requirements.txt

# 2. Offline (sim determinista)
$env:USE_ADAPTERS='true'
$env:USE_NETWORK='false'

# 3. Lanzar UI
streamlit run frontend/app.py
```

## Añadir Claves Reales
```powershell
$env:USE_ADAPTERS='true'
$env:USE_NETWORK='true'
$env:ELEVENLABS_API_KEY='TU_KEY'
$env:MISTRAL_API_KEY='TU_KEY'
streamlit run frontend/app.py
```
> Las rutas reales intentarán llamar al SDK/API; fallos silenciosos hacen fallback determinista.

## Analítica
Estadísticos básicos por sesión:
- `last`, `mean_last_3`, `mean_last_7`, `delta_last`, `pct_change_last`, `severity_trend`, `anomaly` (salto ≥3 o |%| ≥40).

Enriquecido (bootstrap y correlaciones):
```jsonc
{
	"pain_mean_ci": [low, high],
	"corr_pain_mood": r?,
	"corr_pain_mood_ci": [low, high],
	"corr_pain_sleep": r?,
	"corr_pain_sleep_ci": [low, high]
}
```
Interpretación: exploratorio, no diagnóstico clínico. CIs generados con 400 resamples (percentil). Si insuficientes muestras (<4) se omiten.

### Ejemplo de Resumen de Transcripción
```jsonc
{
	"location_keywords": ["espalda", "lumbar"],
	"triggers": ["levantarme"],
	"aggravators": ["correr"],
	"improvement": null,
	"mood_hint": "ansioso",
	"sleep_quality": "bad"
}
```

## Extensiones Futuras (Roadmap)
- STT real streaming con actualización incremental de resumen.
- Refinado de heurísticas: scoring bayesiano de utilidad de pregunta.
- Intervenciones con temporizador y registro de adherencia post‑sugerencia.
- Export parcial (filtros por rango de fechas / tipos de evento).
- Cifrado con rotación de claves y compartición segura (envelope encryption).
- Modelos ligeros on‑device para clasificación de tono emocional.

## Exportación de Sesiones
En pestaña Avanzado:
- Exportación clara (`*.json`).
- Opción “Cifrar exportación (Fernet)”: genera JSON con `{enc, salt, token}`.
- Para descifrar: usar `decrypt_json(token_payload, password)` (ver `backend/src/utils/encryption.py`).
Advertencia: la contraseña no se almacena; si se pierde, no es recuperable.

### Política de Contraseña (Export Cifrada)
- Longitud mínima: 10 caracteres
- Debe incluir al menos 1 letra y 1 dígito
- Recomendado: ≥14 caracteres y símbolo especial para mayor entropía
Si no cumple, el botón de cifrado se deshabilita y se muestra el motivo.

## Tests Rápidos
```powershell
pytest -q
```
Categorías cubiertas: resumen transcripción, guía adaptativa, intervención multi‑modal, cifrado roundtrip, WAV fallback RIFF.

### Smoke / Load Simulation
Script para validar rendimiento básico y ausencia de errores bajo carga sintética:
```powershell
python scripts/load_simulation.py --patients 8 --cycles 6 --output sim_summary.json
```
Genera métricas: latencias (p50, p95), recuento de tipos de intervención y errores.

### Scripts de Seguridad y Mantenimiento
```powershell
# Escaneo de seguridad (Bandit)
python scripts/security_scan.py

# Generar SBOM (CycloneDX)
python scripts/generate_sbom.py --format json --output sbom.json

# Purgar sesión de un paciente
python scripts/purge_session.py --patient-id patient_ab12cd34
```
Pre-commit (opcional):
```powershell
pip install pre-commit detect-secrets
pre-commit install
```
Esto habilita detección básica de secretos antes de commits.

## Seguridad
Resumen ejecutivo y modelo de amenazas detallado en `SECURITY.md`.

Checklist activa (ver archivo): autenticación, cifrado en reposo, rate limiting y secret scanning pendientes para endurecer despliegues no locales.

## Diseño Offline‑First
1. Intento de adapter si `USE_ADAPTERS=true`.
2. Si no hay clave o red, produce salida determinista (hash de texto para audio, transcript fijo, etc.).
3. Esto mantiene reproducibilidad (mismos bytes para mismo input).

## Seguridad y Privacidad (Base)
- No se envían datos de usuario a terceros sin `USE_NETWORK=true` + clave.
- Persistencia local legible para auditoría manual.
- Futuro: cifrado local, consentimiento granular UI (ya soportado a nivel servicio).
- Ver `SECURITY.md` para modelo de amenazas completo y roadmap.

## Contribución
Pull Requests: centrarse en mantener rutas offline intactas y aislar dependencias de red detrás de banderas. Añadir tests para cada nueva ruta de red.

---
© 2025 CeroDolor – En evolución.
