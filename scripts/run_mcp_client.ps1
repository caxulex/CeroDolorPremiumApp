#!/usr/bin/env pwsh
param(
  [string]$BaseUrl = "http://localhost:3000",
  [string]$HealthPath = "/health",
  [string]$EchoPath = "/echo",
  [string]$PayloadFile = "",
  [switch]$Send
)
$ErrorActionPreference = 'Stop'

$python = "C:/Users/caxul/CeroDolorPreminumApp/.venv/Scripts/python.exe"
$script = "c:/Users/caxul/CeroDolorPreminumApp/backend/src/mcp/client.py"

if ($Send) {
  & $python $script --base-url $BaseUrl --health-path $HealthPath --echo-path $EchoPath --send $(if ($PayloadFile) { "--payload-file `"$PayloadFile`"" } )
} else {
  & $python $script --base-url $BaseUrl --health-path $HealthPath --echo-path $EchoPath --probe
}
