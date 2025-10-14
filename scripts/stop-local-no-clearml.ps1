Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Write-Host "=== FBA Local GUI Stop (No ClearML) ==="

# Resolve repo root
$scriptRoot = $PSScriptRoot
if (-not $scriptRoot) {
  $scriptRoot = Split-Path -Parent $PSCommandPath
}
$repoRoot = (Resolve-Path (Join-Path $scriptRoot "..")).Path
Set-Location $repoRoot

# Stop background jobs
Write-Host "-- Stopping background jobs --"
Get-Job -Name "fba-api" -ErrorAction SilentlyContinue | Stop-Job -Force -ErrorAction SilentlyContinue
Get-Job -Name "fba-api" -ErrorAction SilentlyContinue | Remove-Job -Force -ErrorAction SilentlyContinue
Get-Job -Name "fba-frontend" -ErrorAction SilentlyContinue | Stop-Job -Force -ErrorAction SilentlyContinue
Get-Job -Name "fba-frontend" -ErrorAction SilentlyContinue | Remove-Job -Force -ErrorAction SilentlyContinue
Write-Host "Background jobs stopped."

# Stop containers (ignore errors if absent)
Write-Host "-- Stopping containers --"
docker stop fba-redis-dev 2>$null
docker rm fba-redis-dev 2>$null
docker stop fba-postgres-local 2>$null
# Do not remove postgres container/volume to preserve data

Write-Host "Containers stopped."

Write-Host ""
Write-Host "Note: To clean the PostgreSQL data volume (WARNING: data loss):"
Write-Host "# docker volume rm postgres_data"
Write-Host "# (Run manually if desired)"

exit 0