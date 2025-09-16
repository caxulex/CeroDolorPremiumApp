#!/usr/bin/env pwsh
param(
  [string]$PayloadFile = "backend/samples/router_payload.custom.json",
  [string]$Python = "C:/Users/caxul/CeroDolorPreminumApp/.venv/Scripts/python.exe"
)

$ErrorActionPreference = 'Stop'

Write-Host "Running router with payload file: $PayloadFile"
& $Python backend/src/agents/router.py --payload-file $PayloadFile | Tee-Object -FilePath "backend/router.output.json"
Write-Host "Output saved to backend/router.output.json"