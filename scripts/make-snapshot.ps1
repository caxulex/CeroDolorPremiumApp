param(
    [string]$OutputDir = "checkpoints"
)

# Ensure output dir exists
New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null

$ts = Get-Date -Format "yyyyMMdd-HHmmss"
$zipPath = Join-Path $OutputDir "snapshot-$ts.zip"

# Exclude common heavy/volatile dirs
$excludes = @(
  ".git",
  ".venv",
  ".ruff_cache",
  ".pytest_cache",
  "__pycache__",
  "node_modules"
)

Write-Host "Creating snapshot: $zipPath"

# Build file list respecting excludes
$items = Get-ChildItem -LiteralPath . -Recurse -Force |
  Where-Object {
    $rel = $_.FullName.Substring((Get-Location).Path.Length + 1)
    -not ($excludes | ForEach-Object { $rel -like "$_*" -or $rel -like "*\$_*" } | Where-Object { $_ })
  }

# Create zip
Add-Type -AssemblyName System.IO.Compression.FileSystem
$zip = [System.IO.Compression.ZipFile]::Open($zipPath, [System.IO.Compression.ZipArchiveMode]::Create)
try {
  foreach ($item in $items) {
    if ($item.PSIsContainer) { continue }
    $relPath = Resolve-Path -LiteralPath $item.FullName | ForEach-Object { $_.Path.Substring((Get-Location).Path.Length + 1) }
    [System.IO.Compression.ZipFileExtensions]::CreateEntryFromFile($zip, $item.FullName, $relPath) | Out-Null
  }
}
finally {
  $zip.Dispose()
}

# Verify by listing and computing SHA256
Write-Host "Verifying archive..."
try {
  $tmpDir = Join-Path $env:TEMP "cdp-verify-$ts"
  New-Item -ItemType Directory -Path $tmpDir -Force | Out-Null
  [System.IO.Compression.ZipFile]::ExtractToDirectory($zipPath, $tmpDir)
  $hash = Get-FileHash -Algorithm SHA256 -Path $zipPath
  Write-Host ("OK {0}  {1}" -f $hash.Hash, $zipPath)
} catch {
  Write-Error "Verification failed: $($_.Exception.Message)"
  exit 1
} finally {
  if (Test-Path $tmpDir) { Remove-Item -Recurse -Force $tmpDir }
}
