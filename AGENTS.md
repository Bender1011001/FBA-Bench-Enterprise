# Repository Guidelines

## Project Structure & Module Organization
- Source lives under `src/` with installable packages (see `pyproject.toml`). Key domains include `fba_bench_core`, `fba_bench_api`, `agents`, `agent_runners`, `benchmarking`, `scenarios`, `plugins`, and `fba_events`.
- Tests are under `tests/` (e.g., `tests/unit`, `tests/integration`, `tests/contracts`, `tests/validation`, `tests/performance`).
- Ops/config: `alembic/` (migrations), `config/` and `configs/` (YAML), `scripts/` (utilities), `docs/` (documentation), `artifacts/` and `results/` (generated outputs).
- Prefer absolute imports from `src` packages (pytest uses importlib mode).

## Build, Test, and Development Commands
- Install: `poetry install` (requires Poetry). Activate tools with `poetry run ...`.
- Lint: `make lint` (ruff static checks).
- Format: `make format-check` / `make format-fix` (ruff-format + black).
- Types: `make type-check` (mypy strict on `src/`).
- Tests (fast/CI parity):
  - Contracts: `make test-contracts`
  - Full suite + coverage: `make test-all`
  - Local CI bundle: `make ci-local`
- DB migrate (API): `make be-migrate`.

## Coding Style & Naming Conventions
- Python 3.9–3.12 supported. 4-space indent, max line length 100.
- Tools: ruff (lint), black (format), isort profile=black, mypy strict.
- Naming: modules/functions `snake_case`, classes `PascalCase`, constants `UPPER_SNAKE_CASE`.
- Keep public APIs typed; avoid cyclic imports; prefer small, focused modules under `src/`.

## Testing Guidelines
- Framework: pytest with markers `unit` and `integration`; default run skips integration.
- Run all unit/contract tests before pushing: `poetry run pytest -q` and `make test-contracts`.
- Run integration explicitly when relevant: `poetry run pytest -m integration -v`.
- Place tests alongside domain folders in `tests/` using `test_*.py`; add fixtures in `tests/fixtures/`.
- Coverage is collected in `make test-all` (generates `.coverage` and `coverage.xml`).

## Commit & Pull Request Guidelines
- Use Conventional Commits: `feat(scope): ...`, `fix(scope): ...`, `chore: ...`, `ci: ...`.
- PRs must include: clear description, rationale, screenshots or logs when UI/API behavior changes, and linked issue.
- Ensure `make ci-local` passes and pre-commit hooks are installed: `make pre-commit-install` then `make pre-commit-run`.

## Security & Configuration
- Do not commit secrets. Use `.env` locally (see `.env.example`) and Pydantic Settings for config.
- Pin service versions in configs; run alembic migrations before API tests.
