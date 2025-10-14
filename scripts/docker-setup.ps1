# FBA-Bench Docker Setup Script for Windows PowerShell
# Feature parity with scripts/docker-setup.sh and scripts/docker-setup.bat
# Usage:
#   powershell -ExecutionPolicy Bypass -File scripts\docker-setup.ps1 start|stop|restart|logs|reset|update|status
# Defaults to "start" when no command is provided.

[CmdletBinding()]
param(
  [ValidateSet('start','stop','restart','logs','reset','update','status')]
  [string]$Command = 'start',
  [string]$Service
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# Console UTF-8
try { [Console]::OutputEncoding = [Text.Encoding]::UTF8 } catch {}
$PSDefaultParameterValues['Out-File:Encoding']    = 'utf8'
$PSDefaultParameterValues['Add-Content:Encoding'] = 'utf8'
$PSDefaultParameterValues['Set-Content:Encoding'] = 'utf8'

function Info($m){ Write-Host "[INFO] $m" -ForegroundColor Cyan }
function Ok  ($m){ Write-Host "[SUCCESS] $m" -ForegroundColor Green }
function Warn($m){ Write-Host "[WARNING] $m" -ForegroundColor Yellow }
function Err ($m){ Write-Host "[ERROR] $m" -ForegroundColor Red }

function Resolve-DockerCompose {
  # Prefer "docker compose" plugin; fallback to legacy docker-compose
  & docker compose version 2>$null 1>$null
  if ($LASTEXITCODE -eq 0) { return @('docker','compose') }
  if (Get-Command docker-compose -ErrorAction SilentlyContinue) { return @('docker-compose') }
  throw "Docker Compose is not installed. Install Docker Desktop or docker-compose CLI."
}

function Assert-DockerReady {
  if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw "Docker is not installed. Install Docker Desktop first."
  }
  & docker info 1>$null 2>$null
  if ($LASTEXITCODE -ne 0) {
    throw "Docker is not running. Start Docker Desktop and try again."
  }
}

function Invoke-Compose {
  param(
    [Parameter(Mandatory=$true)][string[]]$Args
  )
  $dc = Resolve-DockerCompose
  & $dc @Args
  if ($LASTEXITCODE -ne 0) {
    throw "Compose command failed: $($dc -join ' ') $($Args -join ' ')"
  }
}

function Start-Services {
  Assert-DockerReady
  Info "Starting FBA-Bench services..."
  Invoke-Compose -Args @('up','--build','-d')

  # Readiness probe for API
  $url = "http://localhost:8000/api/v1/health"
  Info "Waiting for API readiness at $url ..."
  $ready = $false
  for ($i=0; $i -lt 30; $i++) {
    try {
      $r = Invoke-WebRequest -UseBasicParsing -Method GET -Uri $url -TimeoutSec 3
      if ($r.StatusCode -ge 200 -and $r.StatusCode -lt 600) { $ready = $true; break }
    } catch {}
    Start-Sleep -Seconds 2
  }
  if ($ready) {
    Ok "API responded."
  } else {
    Warn "API did not respond within timeout. Use '$(Resolve-DockerCompose -join ' ') logs api' to inspect."
  }

  ""
  Ok "Services are up."
  Info "API: http://localhost:8000"
  Info "Logs: $(Resolve-DockerCompose -join ' ') logs -f api"
}

function Stop-Services {
  Assert-DockerReady
  Info "Stopping services..."
  Invoke-Compose -Args @('down')
  Ok "Services stopped."
}

function Restart-Services {
  Stop-Services
  Start-Services
}

function Show-Logs {
  Assert-DockerReady
  if ($Service) {
    Invoke-Compose -Args @('logs','-f',$Service)
  } else {
    Invoke-Compose -Args @('logs','-f')
  }
}

function Reset-Installation {
  Assert-DockerReady
  Warn "This will remove all containers, networks, and volumes created by Compose."
  $ans = Read-Host "Proceed? (y/N)"
  if ($ans -match '^(y|Y)$') {
    Info "Removing Compose artifacts..."
    Invoke-Compose -Args @('down','-v')
    Ok "Reset completed."
  } else {
    Info "Reset cancelled."
  }
}

function Update-Installation {
  Assert-DockerReady
  Info "Updating repository (git pull) and rebuilding images..."
  if (Get-Command git -ErrorAction SilentlyContinue) {
    try { & git pull } catch { Warn "git pull failed or repo not initialized. Continuing." }
  } else {
    Warn "git not installed; skipping pull."
  }
  Invoke-Compose -Args @('build','--no-cache')
  Invoke-Compose -Args @('up','-d')
  Ok "Services updated and running."
}

function Show-Status {
  Assert-DockerReady
  Invoke-Compose -Args @('ps')
}

switch ($Command) {
  'start'   { Start-Services; break }
  'stop'    { Stop-Services; break }
  'restart' { Restart-Services; break }
  'logs'    { Show-Logs; break }
  'reset'   { Reset-Installation; break }
  'update'  { Update-Installation; break }
  'status'  { Show-Status; break }
  default   { Err "Unknown command '$Command'"; exit 1 }
}