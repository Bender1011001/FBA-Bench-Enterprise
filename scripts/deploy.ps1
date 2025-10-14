# Deploy FBA-Bench via Docker Compose (Windows PowerShell)
# - Validates configuration
# - Builds/updates services
# - Runs post-deploy health checks
# - Optional rollback on failure via previous image tag
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File scripts\deploy.ps1 -Env dev
#   powershell -ExecutionPolicy Bypass -File scripts\deploy.ps1 -Env staging -OverlayPostgres
#   powershell -ExecutionPolicy Bypass -File scripts\deploy.ps1 -Env prod -NewImageTag v3.0.0-rc1 -PrevImageTag v3.0.0-rc0
#
# Notes:
# - Requires Docker Desktop with Compose v2
# - For prod/staging, ensure TLS certs are mounted in ./config/tls (server.crt, server.key)
# - Set DEPLOY_WEBHOOK_URL to a Slack/MS Teams compatible webhook to receive notifications

[CmdletBinding()]
param(
  [Parameter(Mandatory=$true)]
  [ValidateSet('dev','staging','prod')]
  [string]$Env,
  [switch]$OverlayPostgres,
  [string]$NewImageTag = '',
  [string]$PrevImageTag = '',
  [int]$HealthRetries = 30,
  [int]$HealthIntervalSec = 2,
  [int]$TimeoutSec = 3
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
try { [Console]::OutputEncoding = [Text.Encoding]::UTF8 } catch {}
$PSDefaultParameterValues['Out-File:Encoding']    = 'utf8'
$PSDefaultParameterValues['Add-Content:Encoding'] = 'utf8'
$PSDefaultParameterValues['Set-Content:Encoding'] = 'utf8'

function Info($m){ Write-Host "[INFO] $m" -ForegroundColor Cyan }
function Ok  ($m){ Write-Host "[SUCCESS] $m" -ForegroundColor Green }
function Warn($m){ Write-Host "[WARNING] $m" -ForegroundColor Yellow }
function Err ($m){ Write-Host "[ERROR] $m" -ForegroundColor Red }

function Resolve-DockerCompose {
  & docker compose version 1>$null 2>$null
  if ($LASTEXITCODE -eq 0) { return @('docker','compose') }
  if (Get-Command docker-compose -ErrorAction SilentlyContinue) { return @('docker-compose') }
  throw "Docker Compose is not installed."
}

function Assert-DockerReady {
  if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw "Docker is not installed. Install Docker Desktop first."
  }
  & docker info 1>$null 2>$null
  if ($LASTEXITCODE -ne 0) { throw "Docker is not running. Start Docker Desktop and try again." }
}

function Post-Webhook([string]$message, [string]$color = '#36a64f') {
  $url = $env:DEPLOY_WEBHOOK_URL
  if (-not $url) { return }
  $payload = @{
    text = $message
    attachments = @(@{ color = $color; text = $message })
  } | ConvertTo-Json -Depth 5
  try { Invoke-RestMethod -Method Post -Uri $url -ContentType 'application/json' -Body $payload | Out-Null } catch {}
}

# Repo root
$ScriptDir = if ($PSScriptRoot) { $PSScriptRoot } else { Split-Path -Parent $MyInvocation.MyCommand.Path }
$RepoRoot  = [IO.Path]::GetFullPath((Join-Path $ScriptDir '..'))

# Compose file selection
$compose = switch ($Env) {
  'dev'     { 'docker-compose.dev.yml' }
  'staging' { 'docker-compose.staging.yml' }
  'prod'    { 'docker-compose.prod.yml' }
}
$composePath = Join-Path $RepoRoot $compose
if (-not (Test-Path $composePath)) { throw "Compose file not found: $composePath" }

# Env file selection
$envFile = switch ($Env) {
  'dev'     { Join-Path $RepoRoot 'config\env\dev.env' }
  'staging' { Join-Path $RepoRoot 'config\env\staging.env' }
  'prod'    { Join-Path $RepoRoot 'config\env\prod.env' }
}
if (-not (Test-Path $envFile)) {
  if ($Env -eq 'prod') {
    # Fallback to .env if provided
    $defaultDotEnv = Join-Path $RepoRoot '.env'
    if (Test-Path $defaultDotEnv) {
      $envFile = $defaultDotEnv
    } else {
      throw "Environment file not found for $Env. Expected: $envFile or .env"
    }
  } else {
    throw "Environment file not found for $Env. Expected: $envFile"
  }
}

# Optional overlay
$overlayArg = @()
if ($OverlayPostgres) {
  $overlayPath = Join-Path $RepoRoot 'docker-compose.postgres.yml'
  if (-not (Test-Path $overlayPath)) { throw "Overlay requested but missing: $overlayPath" }
  $overlayArg = @('-f', $overlayPath)
}

# Export image tag if provided
if ($NewImageTag) {
  $env:API_IMAGE_TAG = $NewImageTag
  Info "Using API_IMAGE_TAG=$NewImageTag"
}

Push-Location $RepoRoot
try {
  Assert-DockerReady
  $dc = Resolve-DockerCompose

  # Validate configuration before deploy
  $py = if (Get-Command python -ErrorAction SilentlyContinue) { 'python' } elseif (Get-Command py -ErrorAction SilentlyContinue) { 'py -3' } else { $null }
  if (-not $py) { throw "Python not found in PATH. Required for validation scripts." }

  Info "Validating configuration: $envFile"
  & $py "scripts/validate_config.py" --env-file "$envFile"
  $vc = $LASTEXITCODE
  if ($vc -eq 3) { throw "Configuration validation failed (fatal errors)." }
  if ($vc -eq 2) { Warn "Configuration validation reported warnings (continuing)." }
  if ($vc -eq 0) { Ok "Configuration validated." }

  # Build & deploy
  Info "Building and deploying: $compose"
  # Compose respects .env by default; also pass explicit --env-file to load environment file
  & $dc -f "$composePath" @overlayArg --env-file "$envFile" up -d --build
  if ($LASTEXITCODE -ne 0) { throw "Compose up failed." }

  # Health checks
  $urls = @()
  switch ($Env) {
    'dev'     { $urls = @('http://localhost:8000/api/v1/health') }
    'staging' { $urls = @('http://localhost:8000/api/v1/health','https://localhost/nginx-health') }
    'prod'    { $urls = @('http://localhost:8000/api/v1/health','https://localhost/nginx-health') }
  }

  Info "Running health checks: $($urls -join ', ')"
  & $py "scripts/healthcheck.py" --urls ($urls -join ',') --retries $HealthRetries --interval $HealthIntervalSec --timeout $TimeoutSec --allow-insecure
  if ($LASTEXITCODE -ne 0) {
    Err "Health checks failed."
    if ($PrevImageTag) {
      Warn "Attempting rollback to previous image tag: $PrevImageTag"
      $env:API_IMAGE_TAG = $PrevImageTag
      & $dc -f "$composePath" @overlayArg --env-file "$envFile" up -d
      if ($LASTEXITCODE -eq 0) {
        Post-Webhook "FBA-Bench deploy ($Env) failed health checks. Rolled back to $PrevImageTag." '#ff0000'
        throw "Deployment failed; rollback completed."
      } else {
        Post-Webhook "FBA-Bench deploy ($Env) failed health checks. Rollback to $PrevImageTag also failed." '#ff0000'
        throw "Deployment failed; rollback failed."
      }
    } else {
      Post-Webhook "FBA-Bench deploy ($Env) failed health checks (no rollback tag provided)." '#ff0000'
      throw "Deployment failed; no rollback tag provided."
    }
  }

  Ok "Deployment completed successfully for environment: $Env"
  Post-Webhook "FBA-Bench deploy ($Env) succeeded. Tag: $($NewImageTag -or 'latest')." '#36a64f'
}
finally {
  Pop-Location
}