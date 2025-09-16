#!/usr/bin/env pwsh
$ErrorActionPreference = 'Stop'

Write-Host "Running backend router demo (AIP -> ASD -> AIPer)..."
$python = "C:/Users/caxul/CeroDolorPreminumApp/.venv/Scripts/python.exe"
& $python backend/src/agents/router.py | Tee-Object -FilePath "backend/router.output.json"
Write-Host "Output saved to backend/router.output.json"
