$ErrorActionPreference = 'Stop'
if (-not (Test-Path .git)) {
  Write-Error "Run from repo root (folder containing .git)."
}

$submods = @()
$lines = git config --file .gitmodules --get-regexp 'submodule\..*\.path' 2>$null
foreach ($line in $lines) {
  $parts = $line -split '\s+', 2
  if ($parts.Count -lt 2) { continue }
  $path = $parts[1]
  $urlKey = $parts[0] -replace '\.path$', '.url'
  $url = git config --file .gitmodules $urlKey
  if (-not (Test-Path $path)) { continue }
  $sha = (git -C $path rev-parse HEAD)
  $branch = try { (git -C $path rev-parse --abbrev-ref HEAD) } catch { 'detached' }
  $submods += [pscustomobject]@{
    path   = $path
    url    = $url
    sha    = $sha
    branch = $branch
  }
}
$dest = Join-Path "external" "submodules.lock.json"
New-Item -ItemType Directory -Force -Path (Split-Path $dest) | Out-Null
$submods | ConvertTo-Json -Depth 4 | Set-Content -Path $dest -Encoding utf8
Write-Host "Wrote $dest" -ForegroundColor Green
