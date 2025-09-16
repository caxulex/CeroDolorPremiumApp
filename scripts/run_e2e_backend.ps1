#!/usr/bin/env pwsh
param(
  [string]$Python = "C:/Users/caxul/CeroDolorPreminumApp/.venv/Scripts/python.exe"
)
$ErrorActionPreference = 'Stop'
Write-Host "Running E2E backend flow..."
& $Python backend/e2e_flow.py | Tee-Object -FilePath "backend/e2e_flow.output.json"
Write-Host "Output saved to backend/e2e_flow.output.json"
