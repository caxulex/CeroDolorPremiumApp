#!/usr/bin/env pwsh
param(
  [int]$Port = 3000,
  [int]$TimeoutSec = 10,
  [switch]$Foreground
)
$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $PSScriptRoot
$venvPython = Join-Path $repoRoot '.venv' 'Scripts' 'python.exe'
$serverPy = Join-Path $repoRoot 'backend' 'src' 'mcp' 'echo_server.py'

if (-not (Test-Path $serverPy)) { throw "Echo server not found: $serverPy" }

$python = if (Test-Path $venvPython) { $venvPython } else { 'python' }

function Test-Health {
  param([int]$P)
  try {
    $r = iwr -UseBasicParsing -TimeoutSec 2 "http://127.0.0.1:$P/health"
    return ($r.StatusCode -eq 200)
  } catch { return $false }
}

if ($Foreground) {
  Write-Host "Starting echo server (foreground) on port $Port using $python"
  & $python $serverPy --port $Port
  exit $LASTEXITCODE
}

Write-Host "Starting echo server (background) on port $Port using $python"
$proc = Start-Process -FilePath $python -ArgumentList @($serverPy, '--port', $Port) -PassThru -WindowStyle Hidden

# Probe readiness
$ok = $false
1..$([math]::Max(1, [int]([double]$TimeoutSec * 2))) | ForEach-Object {
  if (Test-Health -P $Port) { $ok = $true; return }
  Start-Sleep -Milliseconds 500
}

if ($ok) {
  Write-Host "ECHO_READY http://127.0.0.1:$Port/health (pid=$($proc.Id))"
  exit 0
} else {
  Write-Warning "Echo server did not become ready in $TimeoutSec seconds (pid=$($proc.Id))."
  exit 1
}
