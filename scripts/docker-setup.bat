@echo off
REM FBA-Bench Docker Setup Script for Windows (Compose v2 and v1 compatible)
REM Aligns with service name: "api" as defined in docker-compose.yml

setlocal enabledelayedexpansion

REM Ensure Docker is installed
docker --version >nul 2>&1
if %errorLevel% neq 0 (
  echo [ERROR] Docker is not installed. Install Docker Desktop first.
  echo [INFO] https://docs.docker.com/get-docker/
  exit /b 1
)

REM Ensure Docker is running
docker info >nul 2>&1
if %errorLevel% neq 0 (
  echo [ERROR] Docker is not running. Start Docker Desktop and try again.
  exit /b 1
)

REM Resolve Compose CLI: prefer "docker compose" plugin; fallback to "docker-compose"
set "DC=docker-compose"
docker compose version >nul 2>&1
if %errorLevel%==0 set "DC=docker compose"

REM Optional data directories
if not exist "scenario_results" mkdir scenario_results
if not exist "logs" mkdir logs

if "%1"=="start"   goto :start_services
if "%1"=="stop"    goto :stop_services
if "%1"=="restart" goto :restart_services
if "%1"=="logs"    goto :show_logs
if "%1"=="reset"   goto :reset_installation
if "%1"=="update"  goto :update_installation
if "%1"=="status"  goto :show_status

REM default
if "%1"=="" goto :start_services

echo FBA-Bench Docker Setup Script
echo.
echo Usage: %~nx0 {start^|stop^|restart^|logs^|reset^|update^|status}
echo.
echo Commands:
echo   start     Start services ^(default^)
echo   stop      Stop services
echo   restart   Restart services
echo   logs      Show logs ^(optionally specify service: api^)
echo   reset     Remove containers, networks, and volumes
echo   update    git pull + rebuild images + up -d
echo   status    Show Compose status
exit /b 1

:start_services
echo [INFO] Starting FBA-Bench services...
%DC% up --build -d

echo [INFO] Waiting for API readiness (http://localhost:8000/api/v1/health) ...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$u='http://localhost:8000/api/v1/health'; $ok=$false; for($i=0;$i -lt 30;$i++){ try { $r=Invoke-WebRequest -UseBasicParsing -Method Head -TimeoutSec 2 $u } catch { $r=$null }; if($r){ if ($r.StatusCode -ge 200 -and $r.StatusCode -lt 600){ $ok=$true; break } }; Start-Sleep -Seconds 2 }; if($ok){ exit 0 } else { exit 1 }"
if %errorLevel%==0 (
  echo [SUCCESS] API responded.
) else (
  echo [WARNING] API did not respond within timeout. Use "%DC% logs api" to inspect.
)

echo.
echo [SUCCESS] Services are up.
echo [INFO] API:      http://localhost:8000
echo [INFO] Docs may be gated in protected environments.
echo.
echo [INFO] View logs: %DC% logs -f api
echo [INFO] Stop:      %~nx0 stop
exit /b 0

:stop_services
echo [INFO] Stopping services...
%DC% down
echo [SUCCESS] Services stopped.
exit /b 0

:restart_services
call :stop_services
call :start_services
exit /b 0

:show_logs
if "%2"=="" (
  %DC% logs -f
) else (
  %DC% logs -f %2
)
exit /b 0

:reset_installation
echo [WARNING] This will remove all containers, networks, and volumes.
set /p confirm="Proceed? (y/N): "
if /i "!confirm!"=="y" (
  echo [INFO] Removing Compose artifacts...
  %DC% down -v
  echo [SUCCESS] Reset completed.
) else (
  echo [INFO] Reset cancelled.
)
exit /b 0

:update_installation
echo [INFO] Updating repository and rebuilding images...
git --version >nul 2>&1
if %errorLevel%==0 (
  git pull
) else (
  echo [WARNING] git not available; skipping pull.
)
%DC% build --no-cache
%DC% up -d
echo [SUCCESS] Services updated and running.
exit /b 0

:show_status
%DC% ps
exit /b 0
