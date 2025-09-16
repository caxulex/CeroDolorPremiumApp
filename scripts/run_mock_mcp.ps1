#!/usr/bin/env pwsh
param(
  [string]$Python = "C:/Users/caxul/CeroDolorPreminumApp/.venv/Scripts/python.exe"
)
$ErrorActionPreference = 'Stop'
Write-Host "Running mock MCP server..."
& $Python backend/src/mcp/mock_server.py | Tee-Object -FilePath "backend/mock_mcp.output.json"
Write-Host "Output saved to backend/mock_mcp.output.json"