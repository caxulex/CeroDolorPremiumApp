#!/usr/bin/env pwsh
param(
  [Parameter(Mandatory=$true)][string]$ServerDir,
  [Parameter(Mandatory=$true)][string]$ServerStartCmd,
  [Parameter(Mandatory=$true)][string]$StudioDir,
  [Parameter(Mandatory=$true)][string]$StudioStartCmd,
  [Parameter(Mandatory=$true)][string]$AgentsDir,
  [Parameter(Mandatory=$true)][string[]]$AgentsStartCmd
)
$ErrorActionPreference = 'Stop'

function Start-Proc {
  param(
    [Parameter(Mandatory=$true)][string]$WorkingDir,
    [Parameter(Mandatory=$true)][string]$Command,
    [string]$Name
  )
  if (-not (Test-Path $WorkingDir)) { throw "Missing directory: $WorkingDir" }
  Write-Host "[START] $Name => $Command (cwd=$WorkingDir)"
  $psi = New-Object System.Diagnostics.ProcessStartInfo
  $psi.FileName = 'pwsh'
  $psi.Arguments = "-NoProfile -ExecutionPolicy Bypass -Command `"cd `"$WorkingDir`"; $Command`""
  $psi.WorkingDirectory = $WorkingDir
  $psi.RedirectStandardOutput = $true
  $psi.RedirectStandardError = $true
  $psi.UseShellExecute = $false
  $proc = New-Object System.Diagnostics.Process
  $proc.StartInfo = $psi
  $null = $proc.Start()
  return $proc
}

$procs = @()
$procs += Start-Proc -WorkingDir $ServerDir -Command $ServerStartCmd -Name 'Coral Server'
$procs += Start-Proc -WorkingDir $StudioDir -Command $StudioStartCmd -Name 'Coral Studio'
foreach ($cmd in $AgentsStartCmd) {
  $procs += Start-Proc -WorkingDir $AgentsDir -Command $cmd -Name "Agent: $cmd"
}

Write-Host "All processes started. Press Ctrl+C to stop."
# Simple monitor loop
while ($true) {
  Start-Sleep -Seconds 5
  foreach ($p in $procs) {
    if ($p.HasExited) { Write-Warning "Process exited: $($p.StartInfo.Arguments) code=$($p.ExitCode)" }
  }
}
