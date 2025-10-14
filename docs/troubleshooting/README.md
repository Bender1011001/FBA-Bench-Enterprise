# Troubleshooting Guide

This guide covers common issues for FBA-Bench.

## Quick Checks

- Health: `curl http://localhost:8000/api/v1/health`
- Logs: `docker compose logs -f`
- Env: Verify `.env` (from `.env.example`).

## Installation & Startup

### Docker Not Running

- Symptom: `docker: command not found` or compose fails.
- Fix: Install/start Docker Desktop. Validate: `docker --version`.

### No Compose File

- Symptom: "No compose file found" in one-click.
- Fix: Run from repo root; confirm `docker-compose.oneclick.yml` exists.

### Services Exit Immediately

- Symptom: Containers stop after start.
- Fix: `docker compose ps` for status; `docker compose logs -f` for errors; rebuild: `docker compose up -d --build`.

## Configuration

### API Docs 404

- Cause: Gated in prod (AUTH_ENABLED=true, AUTH_PROTECT_DOCS=true).
- Fix: Dev: Set AUTH_PROTECT_DOCS=false. Prod: Use Bearer token for /openapi.json.

### CORS Errors

- Symptom: Browser blocks requests.
- Fix: Set FBA_CORS_ALLOW_ORIGINS="http://localhost:3000,http://localhost:5173" (comma-separated).

### Rate Limit (429)

- Fix: Increase API_RATE_LIMIT="300/minute".

## Performance

### Slow Dev Startup

- Cause: Poetry install on boot.
- Fix: Pre-build image; allocate more Docker resources.

### High Resource Usage

- Fix: Adjust limits in compose files (e.g., deploy.resources.memory: 2G); use `docker stats`.

### WebSocket Lag

- Cause: Redis issues.
- Fix: Check Redis logs: `docker compose logs redis`; ensure FBA_BENCH_REDIS_URL set.

## Database

### SQLite in Docker

- Note: File in container volume; use `docker cp` for access.

### Postgres Migration

- Set DATABASE_URL="postgresql+asyncpg://user:pass@host:5432/db".
- Run `make be-migrate`.

## Authentication

### 401 Unauthorized

- Fix: Add `Authorization: Bearer <JWT>`; ensure AUTH_JWT_PUBLIC_KEY valid.

### WebSocket 4401

- Fix: Include JWT in subprotocol or query: `ws://host/ws/realtime?token=<JWT>`.

## Docker

### Volume Permissions

- Fix: On Linux, add user to docker group: `sudo usermod -aG docker $USER`.

### Port Conflicts

- Fix: Change mapping (e.g., -p 8001:8000); stop conflicting services.

## ClearML

### No Experiments in UI

- Fix: Configure credentials: Run `clearml-init` or set CLEARML_ACCESS_KEY/SECRET_KEY.
- Local: Use `--with-server`; check ports 8080/8008/8081.

### Agent Not Starting

- Fix: Set CLEARML_API_ACCESS_KEY/SECRET_KEY in .env for dockerized agent.

## Diagnostics

- REST Smoke: `./scripts/smoke/curl-smoke.sh` (bash) or `.\scripts\smoke\curl-smoke.ps1` (PowerShell).
- WS Smoke: `python scripts/smoke/ws_smoke.py`.
- Full Tests: `make test-all`.

## Still Stuck?

Open a GitHub issue with:
- OS, Docker/Python versions
- Logs (.env scrubbed)
- Reproduction steps

See [CONTRIBUTING.md](../CONTRIBUTING.md) for more.
