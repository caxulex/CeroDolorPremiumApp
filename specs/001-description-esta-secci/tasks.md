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