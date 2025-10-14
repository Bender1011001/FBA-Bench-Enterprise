@echo off
setlocal

REM fba-start.bat - Comprehensive one-click startup for FBA-Bench on Windows
REM Orchestrates: .env setup, Docker services (postgres, redis, api), health waits, frontend start, browser open
REM Usage: Run from repo root: scripts\fba-start.bat
REM Requirements: Docker Desktop, Node.js/npm, PowerShell 5.1+, curl (or PowerShell Invoke-WebRequest fallback)
REM Logs to console; stops on error (Ctrl+C to interrupt)

echo ========================================
echo FBA-Bench Startup Script (Windows)
echo ========================================
echo Starting at %date% %time%

REM Set repo root (assume run from root or adjust)
set REPO_ROOT=%~dp0..
cd /d "%REPO_ROOT%"

REM Step 1: .env setup
echo [1/6] Checking/creating .env file...
if not exist .env (
    echo ".env not found. Copying from .env.example..."
    copy .env.example .env >nul
    if errorlevel 1 (
        echo "ERROR: Failed to copy .env.example. Check permissions."
        pause
        exit /b 1
    )
    echo "SUCCESS: .env created from .env.example. Edit with your API keys (e.g., OPENROUTER_API_KEY)."
) else (
    echo ".env exists. Skipping creation."
)

REM Step 2: Start Docker services (postgres, redis, api)
echo [2/6] Starting Docker services (postgres, redis, api)...
docker-compose up -d postgres redis api
if errorlevel 1 (
    echo ERROR: docker-compose up failed. Ensure Docker Desktop is running.
    pause
    exit /b 1
)
echo SUCCESS: Docker services started in detached mode.

REM Step 3: Wait for services healthy
echo [3/6] Waiting for services to become healthy (up to 120s)...
set /a COUNT=0
:HEALTH_LOOP
powershell -Command ^
"$maxWait = 120; $count = 0; ^
while ($count -lt $maxWait) { ^
    & docker exec fba-postgres-1 pg_isready -U postgres -d fba_bench -q 2>$null; $pgHealthy = $LASTEXITCODE -eq 0; ^
    $redisOutput = & docker exec fba-redis-1 redis-cli ping 2>$null; $redisHealthy = $redisOutput -eq 'PONG'; ^
    try { $apiResp = Invoke-WebRequest -Uri 'http://localhost:8000/health' -UseBasicParsing -TimeoutSec 5 -Method Get -ErrorAction SilentlyContinue; $apiHealthy = $apiResp.StatusCode -eq 200 } catch { $apiHealthy = $false }; ^
    if ($pgHealthy -and $redisHealthy -and $apiHealthy) { Write-Host 'All services healthy!'; exit 0 }; ^
    Write-Host \"Waiting... Postgres: $pgHealthy, Redis: $redisHealthy, API: $apiHealthy (attempt $($count+1)/$maxWait)\"; ^
    Start-Sleep 5; $count++ ^
}; ^
Write-Host 'Timeout: Services not fully healthy. Proceeding anyway...'; exit 1" >nul 2>&1
if errorlevel 1 (
    echo WARNING: Health check timed out after 120s. Services may still be starting; check docker logs.
) else (
    echo SUCCESS: All services healthy.
)
REM Additional wait for API Poetry install (common bottleneck)
echo Waiting 30s for API container to fully initialize (Poetry install)...
timeout /t 30 /nobreak >nul

REM Step 4: Start frontend in new terminal
echo [4/6] Starting frontend (Vite dev server on port 5173)...
start "FBA Frontend" cmd /k "cd /d \"%REPO_ROOT%\frontend\" && echo Starting npm run dev... && npm ci && npm run dev"
if errorlevel 1 (
    echo ERROR: Failed to start frontend terminal. Ensure Node.js is installed.
    pause
    exit /b 1
)
echo SUCCESS: Frontend started in new terminal (wait ~20s for Vite to compile).

REM Step 5: Wait for frontend ready
echo [5/6] Waiting for frontend to start (up to 60s)...
powershell -Command ^
"$maxWait = 60; $count = 0; ^
while ($count -lt $maxWait) { ^
    try { $resp = Invoke-WebRequest -Uri 'http://localhost:5173' -UseBasicParsing -TimeoutSec 5 -Method Get -ErrorAction SilentlyContinue; ^
    if ($resp.StatusCode -eq 200) { Write-Host 'Frontend ready!'; exit 0 } } catch {}; ^
    Write-Host \"Waiting for frontend... (attempt !!$($count+1)/$maxWait)\"; ^
    Start-Sleep 5; $count++ ^
}; ^
Write-Host 'Timeout: Frontend may still be compiling. Opening browser anyway...'; exit 0" >nul 2>&1
echo SUCCESS: Frontend ready or timeout reached.

REM Step 6: Open browser
echo [6/6] Opening browser to FBA GUI (http://localhost:5173)...
start http://localhost:5173
echo ========================================
echo Startup complete!
echo ========================================
echo - API: http://localhost:8000 (health: /health, docs: /docs)
echo - Database: localhost:5432 (postgres)
echo - Redis: localhost:6379
echo - GUI Dashboard: http://localhost:5173
echo - Logs: Check Docker (docker-compose logs) or frontend terminal
echo - Stop: docker-compose down ^&^& taskkill /f /im node.exe /t (if needed)
echo - Troubleshooting: See docs/STARTUP.md
echo Press any key to exit...
pause >nul