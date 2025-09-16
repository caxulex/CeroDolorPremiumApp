param(
  [switch]$Record
)
$ErrorActionPreference = 'Stop'
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
  Write-Error "git not found in PATH."
}
Write-Host "Initializing submodules..." -ForegroundColor Cyan
git submodule init
git submodule update --init --recursive
Write-Host "Submodules initialized." -ForegroundColor Green
if ($Record) {
  Write-Host "Recording submodule SHAs..." -ForegroundColor Cyan
  & "$PSScriptRoot/record-submodule-shas.ps1"
}
