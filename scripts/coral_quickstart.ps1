#!/usr/bin/env pwsh
param(
  [string]$Config = "scripts/coral.services.config.ps1",
  [switch]$Setup,
  [string]$Branch = "stabletutorial",
  [string]$ExternalDir = "c:\\Users\\caxul\\CeroDolorPreminumApp\\external"
)
$ErrorActionPreference = 'Stop'

function Test-ConfigPresent {
  param([string]$Path)
  if (Test-Path $Path) { return $true }
  $example = "scripts/coral.services.config.example.ps1"
  if (Test-Path $example) {
    Write-Host "[INIT] Creating config from example: $example → $Path"
    Copy-Item -Path $example -Destination $Path -Force
    Write-Host "[NOTE] Edit $Path to match your local repos before running without -Setup."
    return $true
  }
  Write-Error "Missing config and example: $Path"
  return $false
}

if ($Setup) {
  Write-Host "[SETUP] Cloning Coral repos (branch=$Branch) into $ExternalDir"
  $setupArgs = @(
    '-File', 'scripts/setup_coral_repos.ps1',
    '-TargetDir', $ExternalDir,
    '-UseCoralProtocol',
    '-Branch', $Branch,
    '-RecordVersions'
  )
  & pwsh -NoProfile -ExecutionPolicy Bypass @setupArgs
}

if (-not (Test-ConfigPresent -Path $Config)) { exit 1 }

Write-Host "[LOAD] Config: $Config"
. $Config

function Assert-ConfigVar {
  param([string]$Name, [object]$Value)
  if ($null -eq $Value -or ("$Value").Trim() -eq '') { throw "Missing required config: $Name" }
}

Assert-ConfigVar 'ServerDir' $ServerDir
Assert-ConfigVar 'ServerStartCmd' $ServerStartCmd
Assert-ConfigVar 'StudioDir' $StudioDir
Assert-ConfigVar 'StudioStartCmd' $StudioStartCmd
Assert-ConfigVar 'AgentsDir' $AgentsDir
Assert-ConfigVar 'AgentsStartCmd' $AgentsStartCmd

Write-Host "[RUN] Starting Coral services"

$argsList = @(
  '-NoProfile',
  '-ExecutionPolicy', 'Bypass',
  '-File', 'scripts/run_coral_services.ps1',
  '-ServerDir', "$ServerDir",
  '-ServerStartCmd', "$ServerStartCmd",
  '-StudioDir', "$StudioDir",
  '-StudioStartCmd', "$StudioStartCmd",
  '-AgentsDir', "$AgentsDir",
  '-AgentsStartCmd'
)
$argsList += $AgentsStartCmd

& pwsh @argsList
