# Quick Start Guide

This guide walks you from zero to a running FBA-Bench API with one-click Docker, then shows your first checks and a simple benchmark smoke test. All steps are concrete and copy/paste-ready.

Prerequisites
- Docker Desktop (Windows/macOS) or Docker Engine (Linux)
- Docker Compose v2 (bundled with Docker Desktop as "docker compose")
- Git (recommended to clone/update)
- Open ports: 8000 (API)
- Optional for local scripts: Python 3.11+ (if you plan to run Python smoke/perf scripts)

Repository files referenced:
- One-click compose: [docker-compose.oneclick.yml](../../docker-compose.oneclick.yml:1)
- Example env template: [.env.example](../../.env.example:1)
- FastAPI app factory: [python.function create_app()](../../fba_bench_api/server/app_factory.py:241)
- WebSocket handler: [python.function websocket_realtime()](../../fba_bench_api/api/routes/realtime.py:251)
- REST: snapshot [python.function get_simulation_snapshot()](../../fba_bench_api/api/routes/realtime.py:203), events [python.function get_recent_events()](../../fba_bench_api/api/routes/realtime.py:223)

Security defaults you should know
- Production/staging by default enables JWT auth and gates Swagger docs. See [python.module app_factory](../../fba_bench_api/server/app_factory.py:126).
- The one-click flow creates a local .env that disables auth for convenience (development-friendly).

1) Configure environment (one-time)
Windows (PowerShell):
  scripts\oneclick-configure.ps1

macOS/Linux (bash):
  ./scripts/oneclick-configure.sh

What this does:
- Creates ./.env with sensible local defaults:
  - AUTH_ENABLED=false, AUTH_TEST_BYPASS=true (dev mode)
  - SQLite DB persisted to a volume inside the API container (no local DB to install)
  - Internal Redis URL (provided by compose)
- You can later switch to production-grade settings by starting from [.env.example](../../.env.example:1) and setting AUTH_ENABLED=true, AUTH_JWT_PUBLIC_KEY, and a strict FBA_CORS_ALLOW_ORIGINS.

2) Launch the stack
Windows (PowerShell):
  scripts\oneclick-launch.ps1

macOS/Linux (bash):
  ./scripts/oneclick-launch.sh

Alternatively (any OS) with Docker Compose directly:
  docker compose -f docker-compose.oneclick.yml up -d --build

What starts:
- Redis (with requirepass) and the FastAPI backend (port 8000)
- Healthcheck: GET http://localhost:8000/api/v1/health

3) Verify the API is up
Health:
  curl -sS http://localhost:8000/api/v1/health | jq .

Swagger UI (only when docs aren’t gated and auth is disabled):
- http://localhost:8000/docs
- OpenAPI JSON: http://localhost:8000/openapi.json

If you see 401 for most endpoints, you’re likely running in protected mode (AUTH_ENABLED=true and docs gated). See the Troubleshooting and API docs on how to provide a JWT.

4) First requests (REST)
Simulation snapshot:
  curl -sS http://localhost:8000/api/v1/simulation/snapshot | jq .

Recent events (empty in a fresh start):
  curl -sS "http://localhost:8000/api/v1/simulation/events?limit=5" | jq .

These are backed by [python.module realtime](../../fba_bench_api/api/routes/realtime.py:1).

5) Realtime WebSocket (optional)
- Endpoint: ws://localhost:8000/ws/realtime (alias: /ws/events)
- Protocol: subscribe, unsubscribe, publish, ping. See [python.function websocket_realtime()](../../fba_bench_api/api/routes/realtime.py:251).

Browser (auth disabled) — open DevTools console:
  const ws = new WebSocket("ws://localhost:8000/ws/realtime");
  ws.onmessage = (e) => console.log("MSG:", e.data);
  ws.onopen = () => {
    ws.send(JSON.stringify({type:"subscribe", topic:"demo"}));
    ws.send(JSON.stringify({type:"publish", topic:"demo", data:{hello:"world"}}));
    ws.send(JSON.stringify({type:"ping"}));
  };

If auth is enabled, pass a JWT via Sec-WebSocket-Protocol:
  const jwt = "eyJ..."; // a valid RS256 token
  const ws = new WebSocket("wss://YOUR_API/ws/realtime", ["auth.bearer.token."+jwt]);

6) First benchmark run example
Option A: LLM connectivity smoke (requires OPENAI_API_KEY)
- Script: [python.file run_gpt5_benchmark.py](../../run_gpt5_benchmark.py:1)
Windows (PowerShell):
  $env:OPENAI_API_KEY="sk-..." ; python .\run_gpt5_benchmark.py

macOS/Linux (bash):
  export OPENAI_API_KEY="sk-..." && python ./run_gpt5_benchmark.py

This verifies your environment can reach OpenAI and logs a minimal response.

Option B: API-only quick smoke (no API keys)
- Use curl to hit health and snapshot (above)
- Optional: run REST smoke scripts:
  - Bash: [bash.file scripts/smoke/curl-smoke.sh](../../scripts/smoke/curl-smoke.sh:1)
  - PowerShell: [powershell.file scripts/smoke/curl-smoke.ps1](../../scripts/smoke/curl-smoke.ps1:1)
  API_URL=http://localhost:8000 ./scripts/smoke/curl-smoke.sh
  # or
  .\scripts\smoke\curl-smoke.ps1 -ApiUrl "http://localhost:8000"

7) Common next steps
- Read the API reference for endpoints, JWT auth, rate limits, and WebSocket protocol:
  ./../api/README.md
- Enable JWT for protected environments:
  - Set AUTH_ENABLED=true
  - Provide AUTH_JWT_PUBLIC_KEY (PEM). See [.env.example](../../.env.example:1).
  - Confirm docs gating behavior via [python.module app_factory](../../fba_bench_api/server/app_factory.py:266).
- Configure CORS allow-list for production/staging:
  - FBA_CORS_ALLOW_ORIGINS=https://your.app.example.com,https://console.example.com
  - Wildcards are rejected in protected environments (see [python.module app_factory](../../fba_bench_api/server/app_factory.py:259)).
- Realtime/Redis:
  - Prefer FBA_BENCH_REDIS_URL (rediss:// with password) in production. See [.env.example](../../.env.example:39).

Stopping the stack
Windows (PowerShell):
  scripts\oneclick-stop.ps1

macOS/Linux (bash):
  ./scripts/oneclick-stop.sh

FAQ highlights
- Docs are missing (404): You may be in protected mode; either disable AUTH_PROTECT_DOCS for development, or use a JWT and the /openapi.json file via tooling.
- 401 on API calls: Provide Authorization: Bearer <JWT> or disable auth for local development.
- WebSocket connects but no events: Ensure Redis is up; the server gracefully degrades without Redis and will warn. See [python.module realtime](../../fba_bench_api/api/routes/realtime.py:371).
