#!/usr/bin/env pwsh
param(
  [string]$EnvFile = ".env"
)
$ErrorActionPreference = 'Stop'
if (-not (Test-Path $EnvFile)) { throw "Env file not found: $EnvFile" }
Get-Content $EnvFile | ForEach-Object {
  if (-not $_ -or $_.Trim().StartsWith('#')) { return }
  $parts = $_.Split('=',2)
  if ($parts.Count -eq 2) {
    $name = $parts[0].Trim()
    $val = $parts[1]
    [Environment]::SetEnvironmentVariable($name, $val, 'Process')
    Write-Host "Set $name"
  }
}
