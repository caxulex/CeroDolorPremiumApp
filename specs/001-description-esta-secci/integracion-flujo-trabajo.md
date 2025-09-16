# Integración y Flujo de Trabajo de Desarrollo

Este documento describe cómo integrar Coral con un sistema multi-agente (MAS) existente en Python (p. ej., basado en LangChain) y el flujo de trabajo recomendado para desarrollo local en Windows/PowerShell.

## Principios de Integración
- Coral está diseñado explícitamente para no reemplazar, sino para aumentar, los frameworks de agentes existentes. Los repositorios de ejemplo muestran cómo construir agentes con LangChain y exponerlos como herramientas/servicios dentro del ecosistema Coral. Esto permite al equipo de CeroDolorApp aprovechar sus habilidades existentes en Python y LLM, reduciendo la curva de aprendizaje.
- Contratos primero: modela entradas/salidas con JSON Schema (ver `contracts/`). Esto permite validar, probar y versionar interacciones.
- Transporte intercambiable: el router soporta modo local (subprocesos) y modo MCP (HTTP). Así puedes validar lógica sin red y luego activar Coral cuando los endpoints estén listos.

## Arquitectura Multi‑Agente (MAS) para CeroDolorApp
El verdadero poder se manifiesta al modelar sistemas complejos del mundo real. El manejo del dolor crónico no es una tarea monolítica; es un esfuerzo colaborativo entre paciente, médicos, fisioterapeutas y cuidadores. Un único modelo de IA “caja negra” difícilmente captura la complejidad, los permisos y los roles matizados de este ecosistema.

Coral está diseñado para orquestar un Sistema Multi‑Agente (MAS) que funcione como un “gemelo digital” del equipo de atención. En este repositorio se proponen roles iniciales:

- Agente del Paciente: gestiona datos y preferencias del usuario, auto‑registros y consentimientos.
- Agente del Clínico: accede a conocimientos médicos y puede solicitar datos específicos para evaluación.
- Agente del Fisioterapeuta: recomienda ejercicios personalizados y monitorea actividad/adhesión.

Estos agentes especializados pueden colaborar a través de Coral para lograr un objetivo compartido: mejorar el bienestar del paciente. La arquitectura por roles es explicable y confiable porque refleja un modelo de atención familiar, con permisos diferenciados y trazabilidad.

Contratos MAS en `specs/001-description-esta-secci/contracts/`:
- `patient_to_clinician.json`
- `clinician_to_physio.json`
- `physio_to_patient.json`

## Componentes en este repositorio
- Router multi‑agente: `backend/src/agents/router.py` (local y MCP; flags `--mas-demo` y `--mas-mcp`)
- Cliente MCP mínimo: `backend/src/mcp/client.py`
- Utilidades MCP (mapeo y validación): `backend/src/mcp/mapping.py`, `backend/src/mcp/validation.py`
- Servidor MCP de eco (para pruebas): `backend/src/mcp/echo_server.py`
- UI Streamlit: `frontend/app.py` (paneles local/MCP + panel MAS con toggle MCP)
- Contratos: `specs/001-description-esta-secci/contracts/*.json`
- Scripts: `scripts/` (`setup_coral_repos.ps1`, `run_coral_services.ps1`, `coral_quickstart.ps1`, etc.)
- Pruebas: `tests/` (unitarias e integración)

## Flujo de Trabajo Local (Windows/PowerShell)
1) Preparar entorno Python y dependencias
```pwsh
python -m venv .venv
. .\.venv\Scripts\Activate.ps1
python -m pip install -U pip
# Instalar dependencias del proyecto si aplica (requirements/pyproject)
```

2) Demostración MCP local con servidor de eco
```pwsh
pwsh -File scripts\run_echo_server.ps1 -Port 3001
# Esperar "ECHO_READY ..."
# Probar salud
try { (iwr http://127.0.0.1:3001/health -TimeoutSec 5 -UseBasicParsing).StatusCode } catch { 0 }
```

3) Demostración MAS (local y sobre MCP)
```pwsh
# Local únicamente (sin MCP)
$venv = Join-Path $PWD '.venv/Scripts/python.exe'; if (-not (Test-Path $venv)) { $venv = 'python' }
& $venv backend/src/agents/router.py --mas-demo | cat

# Sobre MCP (requiere servidor de eco arriba)
& $venv backend/src/agents/router.py --mas-demo --mas-mcp | cat
```

4) UI de demo
```pwsh
. .\.venv\Scripts\Activate.ps1
python -m streamlit run frontend/app.py --server.headless true --server.port 8501
```

5) Pruebas
```pwsh
python -m ruff check backend frontend tests
pytest -q
```

## Flujo con Coral (Opcional)
1) Clonar repos de Coral (branch tutorial)
```pwsh
pwsh -File scripts\coral_quickstart.ps1 -Setup -Branch stabletutorial -ExternalDir "C:\Users\caxul\CeroDolorPreminumApp\external"
```

2) Inicializar y editar config de servicios
```pwsh
pwsh -File scripts\coral_quickstart.ps1
# Editar scripts/coral.services.config.ps1 (paths y comandos)
```

3) Iniciar servicios Coral (Server, Studio, Agentes ejemplo)
```pwsh
pwsh -File scripts\coral_quickstart.ps1 -Config scripts/coral.services.config.ps1
```

4) Probar conectividad
```pwsh
pwsh -File scripts\probe_coral_pingpong.ps1 -ProbeCommand "curl http://localhost:3000/health"
```

## Buenas Prácticas
- Mantener “opt‑in” para APIs externas (Mistral, ElevenLabs) mediante variables de entorno.
- Validar contratos en cada salto (router/cliente MCP) para detectar desviaciones temprano.
- CI verde: ruff + pytest siempre limpios; separar pruebas de integración que requieran red.
- Documentar endpoints/paths MCP en `mapping.py` o variables de entorno.

## Próximos Pasos (What's next)
Acciones concretas para la siguiente iteración:

1) Alinear MCP a Coral real (T023.3)
- Mapear endpoints del Coral Server en `backend/src/mcp/mapping.py` y habilitar flags/env para seleccionarlos.
- Añadir probes de integración (salud, handshake, echo) y pruebas marcadas como `integration`.

Ejemplo de variables de entorno para MAS (apuntando a Coral o al eco local):
```pwsh
$env:MCP_BASE_URL = "http://127.0.0.1:3001"  # o URL del Coral Server
$env:MCP_TOOL_PATIENT_TO_CLINICIAN_PATH = "/echo"
$env:MCP_TOOL_CLINICIAN_TO_PHYSIO_PATH = "/echo"
$env:MCP_TOOL_PHYSIO_TO_PATIENT_PATH = "/echo"
```

2) Evolución de contratos MAS
- Agregar enums y formatos (p. ej., estado de ánimo, escalas de dolor, fechas ISO 8601) y restricciones adicionales.
- Extender tests negativos en `tests/unit/test_mas_contracts.py` para cubrir "missing-required" y límites.

3) Enriquecer transcriptos MCP
- Capturar timings por hop, validaciones post-POST y shape de sobre (envelope) por mensaje.
- Exponer en UI (panel MAS) con opción de descarga JSON.

4) Desacoplar agentes como servicios
- Elevar los agentes (Paciente/Clínico/Fisio) a procesos MCP con CLI dedicadas; documentar comandos.
- Mantener ruta local de fallback (subprocesos) para desarrollo sin red.

5) Documentación y DX
- Actualizar `quickstart.md` con el flujo MAS y toggle MCP en Streamlit.
- Añadir README breve para contratos MAS y convenciones de versionado.

6) Calidad continua
- Ejecutar `ruff` y `pytest` en cada cambio; mantener el repo verde.
- Etiquetar pruebas de red como `integration` y protegerlas con variables de entorno.

Comandos útiles
```pwsh
# Iniciar servidor de eco (MCP) local
pwsh -File scripts\run_echo_server.ps1 -Port 3001

# Ejecutar router MAS (local y MCP)
$venv = Join-Path $PWD '.venv/Scripts/python.exe'; if (-not (Test-Path $venv)) { $venv = 'python' }
& $venv backend/src/agents/router.py --mas-demo | cat
& $venv backend/src/agents/router.py --mas-demo --mas-mcp | cat

# UI
python -m streamlit run frontend/app.py --server.headless true --server.port 8501

# Lint y pruebas
python -m ruff check backend frontend tests
pytest -q
```
