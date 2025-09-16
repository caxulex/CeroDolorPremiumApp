# Quickstart Guide

## Prerequisites
- Python 3.11 or higher
- Git
- API keys for ElevenLabs and Mistral AI

## Environment Setup
1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd CeroDolorPreminumApp
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install langchain streamlit elevenlabs mistralai pytest
   ```

4. **Set environment variables**:
   ```bash
   export ELEVENLABS_API_KEY="your-key"
   export MISTRAL_API_KEY="your-key"
   ```
   On Windows PowerShell:
   ```pwsh
   $env:ELEVENLABS_API_KEY = "your-key"
   $env:MISTRAL_API_KEY = "your-key"
   ```

## Running the Application
1. **Start the backend agents**:
   ```bash
   python backend/main.py
   ```

2. **Start the frontend**:
   ```bash
   streamlit run frontend/app.py
   ```

3. **Access the app**:
   Open browser to `http://localhost:8501`

## Testing
- **Run all tests**:
  ```bash
  pytest
  ```

- **Run integration tests**:
  ```bash
  pytest tests/integration/
  ```

## Demo Flow
1. Open the Streamlit app
2. Click "Start Daily Check-in"
3. Speak or type pain level and description
4. Receive empathetic response and intervention suggestion
5. View clinician summary (future feature)

## Backend Router Demo
- Quick local validation of agent message flow (no network by default):
   ```pwsh
   ./scripts/run_backend_demo.ps1
   ```
   Output is saved to `backend/router.output.json`.

## Mock MCP Demo (Envelopes + Transcript)
```pwsh
./scripts/run_mock_mcp.ps1
```
Output is saved to `backend/mock_mcp.output.json`.

## MCP Echo Demo (Local)
Start a local echo server and probe/send with the MCP client shim:
```pwsh
pwsh -File scripts/run_echo_server.ps1 -Port 3000
C:/Users/caxul/CeroDolorPreminumApp/.venv/Scripts/python.exe backend/src/mcp/client.py --base-url http://127.0.0.1:3000 --health-path /health --probe
C:/Users/caxul/CeroDolorPreminumApp/.venv/Scripts/python.exe backend/src/mcp/client.py --base-url http://127.0.0.1:3000 --echo-path /echo --send -p '{"type":"ping","from":"demo"}'
```

Or use the Streamlit MCP panel (auto-starts an echo server on load):
```pwsh
C:/Users/caxul/CeroDolorPreminumApp/.venv/Scripts/python.exe -m streamlit run frontend/app.py --server.headless true --server.port 8501
```

## Coral Protocol Quickstart (Optional)
Use the provided scripts to clone and run Coral Server, Studio, and example agents locally.

See also: `integracion-flujo-trabajo.md` for an end-to-end integration and development workflow (ES).

1) Clone Coral-Protocol tutorial branches and record tool versions:
```pwsh
pwsh -File scripts/coral_quickstart.ps1 -Setup -Branch stabletutorial -ExternalDir "C:\Users\caxul\CeroDolorPreminumApp\external"
```

2) Initialize a runtime config (first run copies example):
```pwsh
pwsh -File scripts/coral_quickstart.ps1
```
Then edit `scripts/coral.services.config.ps1` paths/commands as needed.

3) Start all services using your config:
```pwsh
pwsh -File scripts/coral_quickstart.ps1 -Config scripts/coral.services.config.ps1
```

4) Probe connectivity (adjust ports/commands per your services):
```pwsh
pwsh -File scripts/probe_coral_pingpong.ps1 -ProbeCommand "curl http://localhost:3000/health"
```

## End-to-End Flow (Text → Analysis → Suggestion → Optional TTS)
```pwsh
./scripts/run_e2e_backend.ps1
```
Output is saved to `backend/e2e_flow.output.json`. If `ELEVENLABS_API_KEY` is set, a `backend/e2e_suggestion.wav` may be produced.

## Environment Flags
- Real APIs are opt-in. Without keys, code falls back to deterministic placeholders.
   - `ELEVENLABS_API_KEY` enables TTS/STT helpers in backend services.
   - `MISTRAL_API_KEY` enables analysis/suggestion helpers (ASD/AIPer).
   - To avoid accidental network calls in tests/CI, set Mistral to opt-in:
      ```pwsh
      $env:USE_MISTRAL = "1"   # only when you want to call Mistral
      ```

## Troubleshooting
- Ensure API keys are set
- Check Python version: `python --version`
- If voice doesn't work, verify ElevenLabs key and internet connection