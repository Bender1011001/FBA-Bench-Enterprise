# FBA-Bench Startup Guide

This guide provides instructions for starting the FBA-Bench application using the new simplified Docker Compose setups. These replace the previous multi-file configuration, reducing complexity while providing two tailored modes: a full researcher stack and a lightweight test setup. The goal is a streamlined one-click experience via shell scripts (`oneclick-*.sh`) with `--full` or `--test` flags.

## Prerequisites

Before starting, ensure the following are installed and configured:

- **Docker Desktop**: Required for all services (Postgres/SQLite, Redis, API, frontend, and optional observability tools). Download from [docker.com](https://www.docker.com/products/docker-desktop/). Start Docker and ensure it's running (check system tray).
- **Node.js and npm**: Version 18+ for the frontend (Vite dev server). Download from [nodejs.org](https://nodejs.org/). Verify: `node --version` and `npm --version`.
- **Poetry**: Python dependency manager for the backend (handled in Docker, but useful for local dev). Install via `pip install poetry` or [official guide](https://python-poetry.org/docs/#installation). Verify: `poetry --version`.
- **Git**: To clone the repo if needed. Verify: `git --version`.
- **Bash-compatible shell** (e.g., Git Bash on Windows, or WSL): For the one-click scripts. PowerShell alternatives (`oneclick-*.ps1`) are available in `scripts/`.
- **curl** (optional): For health checks; install via package manager if needed.

**Hardware**: At least 4GB RAM free (more for full setup: 8GB+ recommended), 2 CPU cores.

**Ports**: Ensure the following are free (varies by mode):
- Test: 8000 (API), 5173 (Frontend), 5432 (Postgres), 6379 (Redis), 3000 (Grafana light), 9090 (Prometheus light).
- Full: 80 (Nginx/App), 8080 (ClearML), 3000 (Grafana), 9090 (Prometheus), 9200 (Elasticsearch), plus others.

Kill conflicting processes if needed (e.g., `netstat -ano | findstr :8000` on Windows).

## Quick Start with FBA CLI

The FBA CLI provides a single-command entry point for starting and stopping the application after installing dependencies with Poetry. This is now the primary and recommended startup method for simplicity, integrating configuration, launch, health checks, and browser opening in one step. Scripts remain available as a fallback.

### Prerequisites

- Docker installed and running.
- Repository cloned.
- Poetry installed and dependencies installed: `poetry install`

### Usage

Run commands with `poetry run fba ...` (or add the project to your PATH for direct `fba` usage).

- `poetry run fba run test`: Launches the lightweight test setup, handles .env configuration if missing (prompts for keys like API credentials), waits for health checks, and automatically opens http://localhost:5173 in the browser.
- `poetry run fba run full`: Launches the full researcher stack, prompts for additional configurations like ClearML if needed, waits for health checks, and opens http://localhost:80 in the browser.
- `poetry run fba stop test`: Stops the test setup.
- `poetry run fba stop full`: Stops the full setup.

### Example

```bash
poetry install
poetry run fba run test
```

## Simplified Docker Compose Setups

The project now uses two main Docker Compose files to simplify startup:

- **docker-compose.full.yml**: Full researcher stack including ClearML for experiments, comprehensive observability (Prometheus, Grafana, Alertmanager, Jaeger), Postgres, Redis, API, and frontend. Ideal for complex benchmarking with all features enabled.
- **docker-compose.test.yml**: Lightweight single-user testing setup with core API (SQLite option for simplicity), Redis, frontend, basic Postgres, and light monitoring. Supports key features like simulations, agents, and leaderboards without overhead.

These supersede the old multiple Compose files (e.g., `docker-compose.yml`, `docker-compose.oneclick.yml`), reducing configuration complexity and startup time. Use the provided scripts for a one-click experience, or run Docker Compose directly.

The scripts (`oneclick-configure.sh`, `oneclick-launch.sh`, `oneclick-stop.sh`) support `--full` and `--test` flags. On Windows, use the `.ps1` equivalents or Git Bash.

## Configuration

1. Clone the repository (if not already):
   ```
   git clone <repo-url> fba-bench
   cd fba-bench
   ```

2. Install dependencies with Poetry (required for CLI):
   ```
   poetry install
   ```

3. Set up the environment file:
   - Copy `.env.example` to `.env`:
     ```
     cp .env.example .env
     ```
   - Edit `.env` with your API keys (e.g., `OPENROUTER_API_KEY=sk-or-v1-...` from [openrouter.ai](https://openrouter.ai/keys)). Do not commit secrets.

   The FBA CLI (`fba run test` or `fba run full`) will handle .env if missing by prompting for values. Alternatively, use the configuration script as a fallback to generate and prompt for `.env` (recommended for first-time setup without CLI):
   ```
   ./scripts/oneclick-configure.sh [--full | --test]
   ```
   - `--full`: Sets up for researcher mode (prompts for all creds, including observability).
   - `--test`: Defaults for solo testing (simpler prompts, enables SQLite option).
   - This copies `.env.example`, prompts for missing values, and validates basics.

The CLI is the preferred method for configuration during startup, with scripts as fallback.

## Starting the Application

### Full Researcher Setup

For the complete stack with experiments and observability:

- Using the CLI (recommended):
  ```
  poetry run fba run full
  ```
  This starts all services in detached mode, handles configuration if needed, waits for health checks, launches the frontend dev server, and opens the browser.

- Using the script (fallback):
  ```
  ./scripts/oneclick-launch.sh --full
  ```
  This starts all services in detached mode, waits for health checks, launches the frontend dev server, and opens the browser.

- Direct Docker Compose:
  ```
  docker compose -f docker-compose.full.yml up -d
  ```
  Then manually start the frontend: `cd frontend && npm ci && npm run dev`.

**Ports and Access**:
- 80: Main app (Nginx frontend proxy).
- 8080: ClearML web UI for experiments.
- 3000: Grafana dashboard.
- 9090: Prometheus metrics.
- 9200: Elasticsearch (for logs/search).
- API: Accessible via proxy at 80; direct at internal ports.
- Full logs: `docker compose -f docker-compose.full.yml logs -f`.

Includes all features for complex benchmarking, such as multi-agent simulations, cost tracking, and adversarial testing.

Expected startup time: 3-5 minutes (first run longer due to image builds and Poetry install).

Access: http://localhost (main app). Wait ~30s for frontend compile.

### Test/Solo Setup

For lightweight testing with core features:

- Using the CLI (recommended):
  ```
  poetry run fba run test
  ```
  This starts services, handles configuration if needed, waits for health, launches frontend, and opens the browser. Uses SQLite for the database by default (set `DB_USE_POSTGRES=false` in `.env` if preferred).

- Using the script (fallback):
  ```
  ./scripts/oneclick-launch.sh --test
  ```
  This starts services, waits for health, launches frontend, and opens the browser. Uses SQLite for the database by default (set `DB_USE_POSTGRES=false` in `.env` if preferred).

- Direct Docker Compose:
  ```
  docker compose -f docker-compose.test.yml up
  ```
  Then manually start the frontend: `cd frontend && npm ci && npm run dev`.

**Ports and Access**:
- 8000: API (FastAPI docs at http://localhost:8000/docs).
- 5173: Frontend (Vite dev server).
- 3000: Grafana (light monitoring).
- 9090: Prometheus (light metrics).
- Health: http://localhost:8000/health.
- Full logs: `docker compose -f docker-compose.test.yml logs -f`.

Supports simulations, agents, leaderboards, and basic benchmarking without full observability overhead.

Expected startup time: 1-2 minutes (faster with SQLite).

Access: http://localhost:5173 (frontend). API at http://localhost:8000.

## Verification

After startup, verify status:

| Component       | Endpoint/Command                                      | Expected Status                          |
|-----------------|-------------------------------------------------------|------------------------------------------|
| API             | `curl http://localhost:8000/health` (test) or via proxy (full) | `{"status": "healthy", ...}` (200 OK)   |
| Database        | `docker compose logs db` (Postgres/SQLite healthy)    | No errors; connections accepted          |
| Redis           | `docker exec fba-redis-1 redis-cli ping`              | `PONG`                                   |
| Frontend        | Browser to http://localhost:5173 (test) or 80 (full)  | Dashboard loads (React app, charts)      |
| Observability (full/test) | http://localhost:3000 (Grafana)                  | Dashboards accessible                    |
| Logs            | `docker compose logs api`                             | No errors; "Application startup complete"|

- Follow logs in real-time: `docker compose logs -f`.
- Frontend console: Check browser dev tools (F12) for JS errors.
- Test a simulation via GUI or API (e.g., POST /api/v1/simulations/start).

If all healthy, the setup is ready.

## Stopping and Cleanup

- Using the CLI (recommended):
  ```
  poetry run fba stop test  # or full
  ```
  This stops services, kills frontend processes, and cleans up.

- Using the script (fallback):
  ```
  ./scripts/oneclick-stop.sh [--full | --test]
  ```
  This stops services, kills frontend processes, and cleans up.

- Direct Docker Compose:
  ```
  docker compose -f docker-compose.full.yml down  # or .test.yml
  ```
  For full cleanup (removes volumes/DB data): `docker compose down -v`.

- Kill frontend manually if needed: `pkill -f "npm run dev"` or `taskkill /f /im node.exe` (Windows).

- Remove images to free space: `docker compose down --rmi all`.

The CLI is the preferred method for stopping, with scripts as fallback.

## Troubleshooting

### Common Issues

1. **Docker Not Running**:
   - Error: "docker compose up failed".
   - Fix: Start Docker Desktop. On Windows, ensure WSL2 enabled (Settings > General).
   - Verify: `docker --version` and `docker compose version`.

2. **Port Conflicts**:
   - Error: "Bind address already in use".
   - Fix: Kill processes (e.g., `netstat -ano | findstr :8000` then `taskkill /PID <pid> /F` on Windows). Or edit ports in the Compose file/.env.
   - Common: Local DBs, other dev servers.

3. **.env Missing or Invalid**:
   - Error: Logs show "Missing API key" or auth failures.
   - Fix: The CLI will prompt during `fba run`; otherwise, run `./scripts/oneclick-configure.sh` again or edit `.env`. Restart: `docker compose restart api`.
   - Note: Set `AUTH_ENABLED=false` in .env for dev mode.

4. **Services Fail to Start**:
   - Symptom: Unhealthy containers.
   - Fix: Check logs: `docker compose logs <service>`. Ensure .env vars are set (e.g., DB creds). For API: `docker compose up --build api` to rebuild.
   - If Poetry issues: Verify pyproject.toml; first run installs deps.

5. **Frontend Not Loading**:
   - Symptom: "Connection refused" or blank page.
   - Fixes:
     - API down: Verify /health first.
     - npm errors: Run `cd frontend && npm ci` manually.
     - CORS: Set `FBA_CORS_ALLOW_ORIGINS=http://localhost:5173` in .env, restart API.
     - Port busy: Kill node processes.

6. **Health Check Timeout**:
   - Warning: Services not ready.
   - Fix: Manual check: `docker compose ps`. Wait extra time for API init (Poetry). View logs: `docker compose logs -f api`.

7. **Database Issues**:
   - Error: Connection refused or Alembic failures.
   - Fix: For test mode, toggle SQLite in .env. For full: `docker compose exec api poetry run alembic upgrade head`. Or set `DB_AUTO_CREATE=true`.

8. **Slow Startup (First Run)**:
   - Docker builds and Poetry take time.
   - Fix: Pre-build: `docker compose build`. Subsequent runs faster.

### CLI-Specific Issues

- **curl not found**: Health checks in the CLI may fail if curl is not installed. Install curl via your package manager (e.g., `apt install curl` on Linux, `choco install curl` on Windows) or skip the health check by setting `SKIP_HEALTH_CHECK=true` in .env if supported.
- **Browser not opening**: Automatic browser opening via the CLI may not work on all operating systems or configurations. Manually open the appropriate URL (http://localhost:5173 for test, http://localhost:80 for full) in your browser.

### Advanced Troubleshooting

- **Full Restart**: `docker compose down -v && docker system prune -f && poetry run fba run test` (data loss warning; use CLI for restart).
- **Logs**: `docker compose logs api | tail -50` or browser console for frontend.
- **Debug Mode**: Add `--no-reload` to uvicorn in Compose file.
- **Resource Limits**: Increase Docker RAM (Settings > Resources > 6GB+ for full).
- **Windows-Specific**: Use Git Bash for .sh scripts or .ps1 versions. Run as admin if permissions issues.

### Known Limitations

- Scripts assume Bash; use .ps1 on pure Windows.
- No auto-migrations in test mode; manual if needed.
- Full setup requires more resources; use test for quick iterations.
- GUI dev mode disables auth; enable for production.
- CLI requires Poetry install; ensure `poetry shell` if using virtual env.

For issues, check [CONTRIBUTING.md](CONTRIBUTING.md) or open a GitHub issue with logs.

Last updated: September 2025