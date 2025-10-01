# FBA-Bench Enterprise Local Development Setup

## Prerequisites
- Python 3.10+ recommended (compatible with 3.9–3.12)
- A virtual environment (venv) is strongly recommended

## Installation Steps

### Using Poetry (Recommended)
1. Ensure Poetry is installed: `pip install poetry` (or use the official installer from [python-poetry.org](https://python-poetry.org/)).

2. From the workspace root (`c:/Users/admin/Downloads/fba`), navigate to the enterprise repo and install:
   ```
   cd repos/fba-bench-enterprise
   poetry install
   ```
   This installs runtime dependencies from [pyproject.toml](pyproject.toml) (FastAPI, SQLAlchemy, Alembic, argon2-cffi, python-dotenv, uvicorn).

### Using Pip
1. Create and activate a virtual environment:
   - Windows: `python -m venv .venv` then `.\.venv\Scripts\Activate.ps1`
   - macOS/Linux: `python3 -m venv .venv` then `source .venv/bin/activate`

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

## Environment Configuration
1. Copy the example environment file:
   ```
   cp .env.example .env
   ```

2. Edit `.env` if desired (defaults are safe for local development):
   - `DATABASE_URL=sqlite:///./enterprise.db` (SQLite for local dev; override for Postgres)
   - Argon2id parameters: `ARGON2_TIME_COST=3`, `ARGON2_MEMORY_COST=65536`, etc. (tune for security/performance)

Poetry automatically loads `.env` via python-dotenv; for pip, it will be loaded in scripts/app startup.

## Database Bootstrap and Migration Commands
Alembic is configured locally in this repo for project-local migrations.

1. Ensure `.env` is copied and `DATABASE_URL` is set.

2. From the enterprise repo directory (`repos/fba-bench-enterprise`), apply migrations:
   - Poetry: `poetry run alembic upgrade head`
   - Pip: `alembic upgrade head`

This applies the initial migration, creating the `users` table with schema: id (UUID string PK), email (unique/indexed), password_hash, created_at/updated_at (timestamps), is_active (bool default True), subscription_status (nullable string).

Verification:
- SQLite: Confirm `enterprise.db` file exists.
- Use a DB viewer or query to verify the `users` table structure.

For Postgres (optional):
- Install `psycopg2-binary`: `poetry add --group dev psycopg2-binary` or `pip install psycopg2-binary`
- Set `DATABASE_URL=postgresql+psycopg2://user:pass@localhost/dbname`
- Ensure Postgres server is running and the database exists.

## Smoke Test: User Store Persistence
After migrations, run the smoke script to validate user insertion/fetch with password hashing.

From the enterprise repo directory:
- Poetry: `poetry run python scripts/smoke_user_store.py`
- Pip: `python scripts/smoke_user_store.py`

Expected output (first run inserts; subsequent detects duplicate and fetches):
```
Password verified successfully.
{"email": "smoke@example.com", "id": "de305d54-75b4-431b-adb2-eb6b9e546014", "is_active": true, "subscription_status": null}
```

On duplicate (second run):
```
User with email 'smoke@example.com' already exists. Skipping insertion.
Password verified successfully.
{"email": "smoke@example.com", "id": "de305d54-75b4-431b-adb2-eb6b9e546014", "is_active": true, "subscription_status": null}
```

This confirms DB connectivity, schema, hashing, and idempotent behavior. If it fails, check `.env` (DATABASE_URL) and re-run migrations.

## Optional: Run the App Locally
Start the FastAPI app with Uvicorn (loads .env, initializes DB connection on startup):
- Poetry: `poetry run python api_server.py`
- Pip: `python api_server.py`

Or directly:
- `uvicorn api.server:app --reload --host 0.0.0.0 --port 8000`

Expected: Server starts successfully at http://localhost:8000 with no DB connection errors. Visit `/docs` for OpenAPI UI (no endpoints yet).
## Running Tests Locally

### Backend Tests
From the workspace root (`c:/Users/admin/Downloads/fba`):
```bash
# Install dependencies (includes pytest and pytest-cov)
pip install -r repos/fba-bench-enterprise/requirements.txt

# Run tests (requires .env with stubbed vars; Stripe is mocked, no real calls)
pytest -q repos/fba-bench-enterprise/tests

# With coverage
pytest --cov=repos/fba-bench-enterprise/api --cov-report=term-missing repos/fba-bench-enterprise/tests
```

Backend tests cover auth (register/login/me) and Stripe (checkout/webhooks/portal) endpoints. Required env vars (e.g., DATABASE_URL=sqlite:///./enterprise.db, JWT_SECRET=CHANGE_ME_DEV, STRIPE_SECRET_KEY=sk_test_CHANGE_ME, etc.) are stubbed in CI with safe placeholders; local runs use your `.env` (use test values only; copy from .env.example and adjust).

### Frontend Tests
```bash
# Frontend client
cd repos/fba-bench-enterprise/frontend
npm i
npm run test

# Web app
cd repos/fba-bench-enterprise/web
npm i
npm run test
```

This runs unit tests for both the auth client library and web app components using Vitest.

### Build Checks (TypeScript Compilation)
```bash
# Frontend client
cd repos/fba-bench-enterprise/frontend
npm run build  # or npx tsc -p . if no build script

# Web app
cd repos/fba-bench-enterprise/web
npm run build  # Vite build
```

Validates TypeScript compilation and bundling; skips if build script missing.

## CI Workflow
The GitHub Actions CI workflow at [.github/workflows/ci.yml](.github/workflows/ci.yml) automates these checks on push and pull requests to any branch:

- Backend: Python 3.10/3.11 matrix tests with pytest-cov (coverage report uploaded as artifact), using isolated SQLite DB and mocked Stripe (no network calls).
- Frontend Client: Node 18.x unit tests (Vitest) and build check.
- Web App: Node 18.x unit tests (Vitest) and build check.

### CI Locally
To run CI-equivalent checks locally:
- Python: `pip install -r repos/fba-bench-enterprise/requirements.txt && pytest -q --cov=api --cov-report=term repos/fba-bench-enterprise/tests`
- Frontend: `cd repos/fba-bench-enterprise/frontend && npm i && npm run test && npm run build` (skip build if no script)
- Web: `cd repos/fba-bench-enterprise/web && npm i && npm run test && npm run build`

Set env vars as in CI (e.g., via export or .env) for consistency.

Caching is enabled for pip/npm to speed up runs. Tests pass with provided env stubs; coverage is optional but collected for critical paths.