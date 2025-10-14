Param()

$ErrorActionPreference = "Stop"

# Resolve repo root and compose file
$repoRoot = (Resolve-Path "$PSScriptRoot\..").Path
$composeFile = Join-Path $repoRoot "docker-compose.oneclick.yml"

if (-not (Test-Path $composeFile)) {
  Write-Error "Compose file not found: $composeFile"
  exit 1
}

Write-Host "==> Stopping containers defined in $composeFile ..."
Push-Location $repoRoot
try {
  docker compose -f "$composeFile" down
} finally {
  Pop-Location
}

Write-Host "==> Stopped."
