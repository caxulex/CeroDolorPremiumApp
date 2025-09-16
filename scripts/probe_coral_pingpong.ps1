#!/usr/bin/env pwsh
param(
  [Parameter(Mandatory=$true)][string]$ProbeCommand,
  [int]$TimeoutSec = 30
)
$ErrorActionPreference = 'Stop'

Write-Host "[PROBE] Executing: $ProbeCommand"
$job = Start-Job -ScriptBlock {
  param($cmd)
  & pwsh -NoProfile -ExecutionPolicy Bypass -Command $cmd
} -ArgumentList $ProbeCommand

if (Wait-Job -Job $job -Timeout $TimeoutSec) {
  Receive-Job -Job $job
  Write-Host "[OK] Probe completed."
  Exit 0
} else {
  Stop-Job -Job $job -Force | Out-Null
  Write-Error "[TIMEOUT] Probe exceeded $TimeoutSec seconds."
  Exit 1
}
