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