#!/usr/bin/env pwsh
param(
  [string]$TargetDir = "c:\\Users\\caxul\\CeroDolorPreminumApp\\external",
  # Defaults set to public reference repos provided in conversation
  [string]$CoralServerUrl = "https://github.com/modelcontextprotocol/servers.git",
  [string]$CoralStudioUrl = "https://github.com/modelcontextprotocol/inspector.git",
  [string]$AgentsExamplesUrl = "https://github.com/lastmile-ai/mcp-agent.git",
  [switch]$Install,
  [ValidateSet('npm','pnpm','yarn')][string]$NodePm = 'npm',
  [string]$Python = '',
  [switch]$RecordVersions,
  [switch]$UseCoralProtocol,
  [string]$Branch = "stabletutorial"
)
$ErrorActionPreference = 'Stop'

Write-Host "Creating external dir at $TargetDir"
New-Item -ItemType Directory -Force -Path $TargetDir | Out-Null

function Clone-IfNeeded {
  param(
    [Parameter(Mandatory=$true)][string]$Name,
    [Parameter(Mandatory=$true)][string]$Url,
    [string]$Branch = ''
  )
  $dest = Join-Path $TargetDir $Name
  if (Test-Path $dest) { Write-Host "[SKIP] Exists: $dest"; return $dest }
  if (-not $Url) { Write-Host "[WARN] No URL provided for $Name. Creating placeholder dir."; New-Item -ItemType Directory -Path $dest | Out-Null; return $dest }
  Write-Host "[CLONE] $Name from $Url → $dest"
  git --version | Out-Null
  if ($Branch) {
    git clone --depth 1 -b $Branch $Url $dest | Write-Host
  } else {
    git clone --depth 1 $Url $dest | Write-Host
  }
  return $dest
}

$serverRepo = if ($UseCoralProtocol) { 'https://github.com/Coral-Protocol/coral-server' } else { $CoralServerUrl }
$studioRepo = if ($UseCoralProtocol) { 'https://github.com/Coral-Protocol/coral-studio' } else { $CoralStudioUrl }

$branchArg = if ($UseCoralProtocol) { $Branch } else { '' }

$serverDir = Clone-IfNeeded -Name 'coral-server' -Url ($serverRepo | ForEach-Object { $_ }) -Branch $branchArg
$studioDir = Clone-IfNeeded -Name 'coral-studio' -Url ($studioRepo | ForEach-Object { $_ }) -Branch $branchArg
$agentsDir = Clone-IfNeeded -Name 'coral-agents-examples' -Url ($AgentsExamplesUrl | ForEach-Object { $_ })

if ($Install) {
  Write-Host "[INSTALL] Attempting to install dependencies"
  foreach ($dir in @($serverDir,$studioDir)) {
    if (-not (Test-Path $dir)) { continue }
    if (Test-Path (Join-Path $dir 'package.json')) {
      Push-Location $dir
      try {
        if ($NodePm -eq 'npm') { npm ci }
        elseif ($NodePm -eq 'pnpm') { pnpm i --frozen-lockfile }
        else { yarn install --frozen-lockfile }
      } finally { Pop-Location }
    }
  }
  if ($agentsDir -and (Test-Path $agentsDir)) {
    # Python agents examples may exist; allow optional venv setup
    if ($Python) {
      $venv = Join-Path $agentsDir '.venv'
      & $Python -m venv $venv
      & (Join-Path $venv 'Scripts' 'python.exe') -m pip install -U pip
      if (Test-Path (Join-Path $agentsDir 'requirements.txt')) {
        & (Join-Path $venv 'Scripts' 'python.exe') -m pip install -r (Join-Path $agentsDir 'requirements.txt')
      }
    }
  }
}

@'
Coral MCP Setup (scaffold)
==========================

This directory holds local clones of Coral MCP components.

Defaults
--------
By default, this script will clone the following public repositories:
- Server: https://github.com/modelcontextprotocol/servers.git (reference servers)
- Studio: https://github.com/modelcontextprotocol/inspector.git (web inspector)
- Agents: https://github.com/lastmile-ai/mcp-agent.git (Python/Node agent examples)

Usage examples:

1) Clone repos (with defaults):

  pwsh -File scripts/setup_coral_repos.ps1

   Or clone specific forks/branches by overriding URLs:

  pwsh -File scripts/setup_coral_repos.ps1 `
    -CoralServerUrl https://github.com/<org>/coral-server.git `
    -CoralStudioUrl https://github.com/<org>/coral-studio.git `
    -AgentsExamplesUrl https://github.com/<org>/coral-agents-examples.git

2) Install dependencies (Node + optional Python):

  pwsh -File scripts/setup_coral_repos.ps1 -Install -NodePm npm -Python "C:\\Path\\to\\python.exe"

4) Clone Coral-Protocol tutorial branches:

  pwsh -File scripts/setup_coral_repos.ps1 -UseCoralProtocol -Branch stabletutorial

3) Start services and agents (provide your start commands):

  pwsh -File scripts/run_coral_services.ps1 `
    -ServerDir .\\external\\coral-server -ServerStartCmd "npm run start" `
    -StudioDir .\\external\\coral-studio -StudioStartCmd "npm run dev" `
    -AgentsDir .\\external\\coral-agents-examples -AgentsStartCmd @("python agent_aip.py","python agent_asd.py","python agent_aiper.py")

Notes:
- Commands above are examples. Use the actual commands provided by each repo.
- These scripts are non-invasive and do not affect tests/CI.
'@ | Set-Content (Join-Path $TargetDir 'README.txt') -Encoding UTF8

Write-Host "Done. Replace placeholder URLs in scripts as needed."

if ($RecordVersions) {
  $readme = Join-Path $TargetDir 'README.txt'
  $toolText = @"

Toolchain Versions
------------------
Timestamp: $(Get-Date -Format o)

"@
  Add-Content -Path $readme -Value $toolText -Encoding UTF8
  try { node --version | ForEach-Object { "Node: $_" } | Add-Content $readme } catch {}
  try { npm --version | ForEach-Object { "npm: $_" } | Add-Content $readme } catch {}
  try { pwsh --version | ForEach-Object { "pwsh: $_" } | Add-Content $readme } catch {}
  if ($Python) {
    try { & $Python --version 2>&1 | ForEach-Object { "Python: $_" } | Add-Content $readme } catch {}
  }
}
