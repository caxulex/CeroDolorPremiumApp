# Tasks: Agente de Empatía Crónica

Input: Design documents from `C:/Users/caxul/CeroDolorPreminumApp/specs/001-description-esta-secci/`
Prerequisites: `plan.md` (required), `research.md`, `data-model.md`, `contracts/`, `quickstart.md`

Feature Directory: `C:/Users/caxul/CeroDolorPreminumApp/specs/001-description-esta-secci`

## Execution Flow (main)
```
1. Load plan.md and extract stack, structure, and constraints
2. Load optional design docs: data-model.md, contracts/, research.md, quickstart.md
3. Generate tasks by category and mark [P] for parallel where safe
4. Enforce TDD ordering: tests before implementation
5. Number tasks T001..Txxx; include file paths and dependency notes
6. Provide parallel execution examples with actual commands
```

Path conventions used (web app): `backend/src/`, `frontend/`, and `tests/` at repo root.

---

## Phase 3.1: Setup
T001 Configure linting and testing runners [backend/.]  
• Files: `pyproject.toml` or Ruff config already present; keep `pytest.ini` as is  
• Commands:  
```pwsh
& .\.venv\Scripts\Activate.ps1
.\.venv\Scripts\python.exe -m ruff check backend
.\.venv\Scripts\python.exe -m pytest -q
```

T002 [P] Add base logging config for backend  
• File: `backend/src/logging_config.py`  
• Purpose: centralize structured logging, INFO default, DEBUG via env  
• Dependency: none

T003 [P] Verify MCP echo utilities available  
• Scripts: `scripts/run_echo_server.ps1`, `scripts/run_mcp_client.ps1`  
• Purpose: ensure local MCP echo path for integration tests  
• Dependency: none

---

## Phase 3.2: Tests First (TDD) — MUST COMPLETE BEFORE 3.3
For each contract JSON schema in `contracts/`, create a contract test that loads the schema and validates a representative payload.

Contracts directory: `C:/Users/caxul/CeroDolorPreminumApp/specs/001-description-esta-secci/contracts/`

T004 [P] Contract test for `aip_to_asd.json`  
• File: `tests/contracts/test_aip_to_asd.py`  
• Validate request/response shape against schema

T005 [P] Contract test for `asd_to_aiper.json`  
• File: `tests/contracts/test_asd_to_aiper.py`

T006 [P] Contract test for `patient_to_clinician.json`  
• File: `tests/contracts/test_patient_to_clinician.py`

T007 [P] Contract test for `clinician_to_physio.json`  
• File: `tests/contracts/test_clinician_to_physio.py`

T008 [P] Contract test for `physio_to_patient.json`  
• File: `tests/contracts/test_physio_to_patient.py`

T009 [P] Contract test for `clinician_report.json` (AIC)  
• File: `tests/contracts/test_clinician_report.py`

T010 [P] Contract test for `research_query.json`  
• File: `tests/contracts/test_research_query.py`

T011 [P] Contract test for `data_offer.json`  
• File: `tests/contracts/test_data_offer.py`

T012 [P] Contract test for `anonymized_data_bundle.json`  
• File: `tests/contracts/test_anonymized_data_bundle.py`

T013 [P] Contract test for `micropayment_receipt.json`  
• File: `tests/contracts/test_micropayment_receipt.py`

T014 [P] Contract test for `audit_log_entry.json`  
• File: `tests/contracts/test_audit_log_entry.py`

T015 [P] Contract test for `data_access_request.json`  
• File: `tests/contracts/test_data_access_request.py`

T016 [P] Contract test for `consent_grant.json`  
• File: `tests/contracts/test_consent_grant.py`

User stories → integration tests (derive from `quickstart.md`):

T017 Daily check-in flow integration test  
• File: `tests/integration/test_daily_checkin_flow.py`  
• Scope: AIP → ASD → AIPer transcript and validations; offline by default  
• Dependency: `scripts/run_backend_demo.ps1` or router entrypoint

T018 Weekly clinician summary integration test  
• File: `tests/integration/test_weekly_clinician_summary.py`  
• Scope: `--include-aic` path in router; validate schema and enrichment  
• Dependency: AIC schema/validator present

T019 [P] Env-guarded network probe tests (adapters)  
• File: `tests/integration/test_integrations_network.py`  
• Skip unless `USE_NETWORK=true`; probe Crossmint/Solana paths  
• Dependency: none

---

## Phase 3.3: Core Implementation (ONLY after tests are failing)
Data model entities from `data-model.md` → Pydantic models and adapters.

T020 [P] Model: Patient  
• File: `backend/src/models/patient.py`  
• Fields: `id: str`, `name: str`, `pain_history: list[PainRecord]`

T021 [P] Model: PainRecord  
• File: `backend/src/models/pain_record.py`  
• Fields: `date: datetime`, `pain_level: int`, `description?: str`, `mood?: str`, `sleep?: str`

T022 [P] Model: Clinician  
• File: `backend/src/models/clinician.py`  
• Fields: `id: str`, `name: str`, `patients: list[str]`

T023 [P] Model: Agent  
• File: `backend/src/models/agent.py`  
• Fields: `type: Literal['AIP','ASD','AIPer','AIC']`, `state: dict | None`

T024 Service wiring: Ensure AIP/ASD/AIPer use models where applicable  
• Files: `backend/src/services/aip_service.py`, `asd_service.py`, `aiper_service.py`  
• Replace ad-hoc dicts with models for internal data shapes

T025 Router: Strict contract mapping and validation  
• File: `backend/src/agents/router.py`  
• Ensure each hop validates input/output against `contracts/` schemas; include per-hop timings

T026 AIC generation & schema validation  
• Files: `backend/src/services/aic_service.py`, `backend/src/mcp/validation.py`  
• Validate against `clinician_report.json`; attach MAS timings to highlights

---

## Phase 3.4: Integration
T027 [P] MCP client/server echo flow validation  
• Files: `backend/src/mcp/client.py`, `backend/src/mcp/echo_server.py`  
• Ensure health/echo paths and transcript capture

T028 Adapter gating and network toggles  
• Files: `backend/src/integrations/*.py`  
• Enforce `USE_ADAPTERS` and `USE_NETWORK` flags; deterministic offline fallbacks

T029 [P] Web3 data wallet offline flow  
• File: `backend/src/services/research_network_service.py`  
• Ensure Crossmint/Solana adapters are used when env flags set; write audit JSONL

---

## Phase 3.5: Polish
T030 [P] Unit tests for models and validators  
• File: `tests/unit/test_models_validation.py`

T031 [P] Performance smoke (latency < 3s)  
• File: `tests/perf/test_latency_budget.py`  
• Measure end-to-end local router cycle with small payload

T032 [P] Docs: Update backend/README.md and RECOVERY.md  
• Files: `backend/README.md`, `RECOVERY.md`

T033 [P] Scripts: One-command demo launcher  
• File: `scripts/run_e2e_backend.ps1`  
• Purpose: set env flags for offline run, invoke router, save outputs

---

## Dependencies
- Phase 3.2 (T004–T019) tests must be authored before Phase 3.3 implementation tasks (T020–T026)
- Models (T020–T023) before service/adapter wiring (T024–T026)
- MCP and adapters (T027–T029) after core router/services (T024–T026)
- Polish (T030–T033) only after prior phases

---

## Parallel Execution Examples
The following [P] tasks can run concurrently in separate terminals (different files, no conflicts):

- Contract tests (T004–T016) — run in parallel
  ```pwsh
  # Terminal A
  .\.venv\Scripts\python.exe -m pytest -q tests\contracts\test_aip_to_asd.py
  # Terminal B
  .\.venv\Scripts\python.exe -m pytest -q tests\contracts\test_asd_to_aiper.py
  # Terminal C
  .\.venv\Scripts\python.exe -m pytest -q tests\contracts\test_clinician_report.py
  ```

- Model stubs (T020–T023) — implement in parallel
  ```pwsh
  # Example creation commands (touch files)
  ni backend/src/models/patient.py -Force | Out-Null
  ni backend/src/models/pain_record.py -Force | Out-Null
  ni backend/src/models/clinician.py -Force | Out-Null
  ni backend/src/models/agent.py -Force | Out-Null
  ```

- Adapter/network probes (T019, T028–T029)
  ```pwsh
  $env:USE_NETWORK = 'true'
  $env:SOLANA_RPC_URL = 'https://api.devnet.solana.com'
  $env:SOLANA_PAYER_SECRET = 'dev-only-secret'
  .\.venv\Scripts\python.exe -m pytest -q tests\integration\test_integrations_network.py
  ```

---

## Validation Checklist
- [ ] All contracts have corresponding tests (T004–T016)
- [ ] All entities have model tasks (T020–T023)
- [ ] Tests precede implementation (TDD enforced)
- [ ] [P] tasks operate on different files (safe parallelism)
- [ ] Each task lists exact file paths

---

Generated from available design artifacts and repository structure on 2025-09-16.
# Tasks: Agente de Empatía Crónica

**Input**: Design documents from `/specs/001-description-esta-secci/`
**Prerequisites**: plan.md (required), research.md, data-model.md, contracts/

## Execution Flow (main)
```
1. Load plan.md from feature directory
   → If not found: ERROR "No implementation plan found"
   → Extract: tech stack, libraries, structure
2. Load optional design documents:
   → data-model.md: Extract entities → model tasks
   → contracts/: Each file → contract test task
   → research.md: Extract decisions → setup tasks
3. Generate tasks by category:
   → Setup: project init, dependencies, linting
   → Tests: contract tests, integration tests
   → Core: models, services, CLI commands
   → Integration: DB, middleware, logging
   → Polish: unit tests, performance, docs
4. Apply task rules:
   → Different files = mark [P] for parallel
   → Same file = sequential (no [P])
   → Tests before implementation (TDD)
5. Number tasks sequentially (T001, T002...)
6. Generate dependency graph
7. Create parallel execution examples
8. Validate task completeness:
   → All contracts have tests?
   → All entities have models?
   → All endpoints implemented?
9. Return: SUCCESS (tasks ready for execution)
```

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- Include exact file paths in descriptions

## Path Conventions
- **Web app**: `backend/src/`, `frontend/src/`
- Paths shown below assume web app structure from plan.md

## Phase 3.1: Setup
- [x] T001 Create project structure: backend/, frontend/, tests/ at repository root
- [x] T002 Initialize Python project with LangChain, ElevenLabs API, Mistral AI API dependencies in backend/
- [x] T003 Configure linting and formatting tools (ruff) in backend/

## Phase 3.2: Tests First (TDD) ⚠️ MUST COMPLETE BEFORE 3.3
**CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation**
- [x] T004 [P] Contract test for aip_to_asd.json in tests/contract/test_aip_to_asd.py
- [x] T005 [P] Contract test for asd_to_aiper.json in tests/contract/test_asd_to_aiper.py
- [x] T006 [P] Integration test for HU-1 daily conversational check-in in tests/integration/test_daily_checkin.py
- [x] T007 [P] Integration test for HU-2 pain registration by voice in tests/integration/test_pain_registration.py
- [x] T008 [P] Integration test for HU-3 mood and sleep registration in tests/integration/test_mood_sleep.py
- [x] T009 [P] Integration test for HU-4 empathetic feedback in tests/integration/test_empathetic_feedback.py
- [x] T010 [P] Integration test for HU-5 proactive interventions in tests/integration/test_proactive_interventions.py
- [x] T011 [P] Integration test for HU-6 clinician summary generation in tests/integration/test_clinician_summary.py

## Phase 3.3: Core Implementation (ONLY after tests are failing)
- [x] T012 [P] Patient model in backend/src/models/patient.py
- [x] T013 [P] PainRecord model in backend/src/models/pain_record.py
- [x] T014 [P] Clinician model in backend/src/models/clinician.py
- [x] T015 [P] Agent model in backend/src/models/agent.py
- [x] T016 AIP agent service conversation logic in backend/src/services/aip_service.py
- [x] T017 ASD agent service data analysis logic in backend/src/services/asd_service.py
- [x] T018 AIPer agent service intervention generation in backend/src/services/aiper_service.py

## Phase 3.4: Integration
- [ ] T019 Clone Coral Server, Coral Studio, and example agents repositories
   - [x] T019.1 Wire defaults into `scripts/setup_coral_repos.ps1` (servers/inspector/mcp-agent)
   - [x] T019.2 Add `-UseCoralProtocol` and `-Branch` to `scripts/setup_coral_repos.ps1` for tutorial branches
   - [x] T019.3 Add `scripts/coral_quickstart.ps1` to orchestrate setup and service start with config file
- [ ] T020 Configure local Python and Node.js environments
   - [x] T020.1 Add `-RecordVersions` to `scripts/setup_coral_repos.ps1` to log Node/npm/Python/Pwsh versions
   - [x] T020.2 Create `.env.example` and `scripts/load_env.ps1` to load MCP/API variables
- [ ] T021 Study and document MCP connection patterns from example agents
   - [x] T021.2 Document reference repos and mapping notes in `specs/001-description-esta-secci/mcp-patterns.md`
   - [x] T021.3 Create integration & dev workflow doc (ES) in `specs/001-description-esta-secci/integracion-flujo-trabajo.md`
- [x] T022 Achieve successful "ping-pong" communication between two simple agents via local Coral Server
   - Implemented a local echo server fallback in `backend/src/mcp/echo_server.py` and validated via `tests/integration/test_mcp_ping_pong.py` and Streamlit MCP panel.
- [x] T022.1 [P] Local router demo (subprocess) chaining AIP→ASD→AIPer in `backend/src/agents/router.py` (Done)
- [x] T022.2 [P] Mock MCP server with envelopes + transcript in `backend/src/mcp/mock_server.py` (Done)
- [x] T021.1 [P] Scaffolding scripts: `scripts/setup_coral_repos.ps1`, `scripts/run_coral_services.ps1`, `scripts/probe_coral_pingpong.ps1` with README usage in `backend/README.md`
- [ ] T023 Establish MCP communication between AIP, ASD, and AIPer agents
   - [x] T023.1 Add MCP transport option to `backend/src/agents/router.py` (flag `--mcp` to use shim/client instead of subprocess)
   - [x] T023.2 Extend Streamlit transcript viewer to ingest real MCP exchange (sources, ids, timings)
   - [ ] T023.3 Align MCP client to Coral Server endpoints as they stabilize; add integration probes
   - [ ] T023.4 Add MAS-over-MCP transcript timings and per-hop validations exposed in UI
- [ ] T024 Connect ElevenLabs API to AIP for STT and TTS (env-guard helpers added; pending real integration)
- [ ] T025 Integrate Mistral AI API into ASD and AIPer for real analysis and recommendations (env-guard helpers added; pending real integration)
- [x] T026 Record complete backend flow test: voice input → transcription → analysis → intervention → voice synthesis
- [x] T022.3 Add contract schema validation in router and mock MCP pipelines to enforce `contracts/aip_to_asd.json` and `contracts/asd_to_aiper.json` in `backend/src/agents/router.py` and `backend/src/mcp/mock_server.py`
 - [x] T022.4 [P] Minimal MCP client shim with contract validation in `backend/src/mcp/client.py`
 - [x] T022.5 [P] PowerShell helper to probe/POST via MCP client shim in `scripts/run_mcp_client.ps1`

## Phase 3.5: Polish
- [x] T027 Build simple Streamlit UI connecting to backend agents in `frontend/app.py` (Done: panels for router and mock MCP demos)
- [x] T027.1 [P] Add transcript viewer panel in Streamlit to visualize MCP envelopes/transcript in `frontend/app.py`
- [ ] T028 Record multiple takes of application demo video
- [ ] T029 Write clear and professional README.md in repository root
- [ ] T030 Design presentation slides (PDF) and cover image
- [ ] T031 Edit and finalize 5-minute presentation video
- [ ] T032 Submit complete project to hackathon with all deliverables

## Dependencies
- Tests (T004-T011) before implementation (T012-T018)
- T012-T015 before T016-T018
- T019-T022 before T023
- T016-T018 before T024-T026
- Implementation before polish (T027-T032)

## Parallel Example
```
# Launch T004-T011 together:
Task: "Contract test for aip_to_asd.json in tests/contract/test_aip_to_asd.py"
Task: "Contract test for asd_to_aiper.json in tests/contract/test_asd_to_aiper.py"
Task: "Integration test for HU-1 daily conversational check-in in tests/integration/test_daily_checkin.py"
... (all integration tests)

# Launch independent MCP scaffolding tasks together:
Task: "T022.4 [P] Minimal MCP client shim in backend/src/mcp/client.py"
Task: "T022.5 [P] Helper script in scripts/run_mcp_client.ps1"

# Example Task agent commands (PowerShell):
pwsh -File scripts/setup_coral_repos.ps1 -RecordVersions
pwsh -File scripts/run_mcp_client.ps1 -ProbeCommand "curl http://localhost:3000/health"
```

## Notes
- [P] tasks = different files, no dependencies
- Verify tests fail before implementing
- Commit after each task
- Avoid: vague tasks, same file conflicts

## Task Generation Rules
*Applied during main() execution*

1. **From Contracts**:
   - Each contract file → contract test task [P]
   - Each endpoint → implementation task
   
2. **From Data Model**:
   - Each entity → model creation task [P]
   - Relationships → service layer tasks
   
3. **From User Stories**:
   - Each story → integration test [P]
   - Quickstart scenarios → validation tasks

4. **Ordering**:
   - Setup → Tests → Models → Services → Endpoints → Polish
   - Dependencies block parallel execution

## Validation Checklist
*GATE: Checked by main() before returning*

- [ ] All contracts have corresponding tests
- [ ] All entities have model tasks
- [ ] All tests come before implementation
- [ ] Parallel tasks truly independent
- [ ] Each task specifies exact file path
- [ ] No task modifies same file as another [P] task

Toolchain Versions
------------------
Timestamp: 2025-09-15T10:25:47.7033220-05:00

pwsh: PowerShell 7.5.3

pwsh -File scripts/setup_coral_repos.ps1 -RecordVersions