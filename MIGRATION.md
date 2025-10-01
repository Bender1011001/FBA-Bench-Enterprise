# FBA-Bench Transition — Phase 1 Migration Guide (Enterprise)

This document describes how the monorepo was bifurcated locally into two staged repositories and how to develop, validate, and prepare for a later public/private push.

- Core (public, source-available): `repos/fba-bench-core`
- Enterprise (private, proprietary): `repos/fba-bench-enterprise`

No remote operations were performed in Phase 1. This guide is for local development and the eventual push to your Git hosting.

## 1) What moved where (authoritative mapping)

- Mapping file (source → destination): `repos/file_split_map.json`
- Execution report: `repos/split_report.json`
- Pending review items: `repos/PENDING_REVIEW.txt`

Status summary at generation time:
- Planned entries copied: see `repos/split_report.json`
- Needs review (not copied): see `repos/PENDING_REVIEW.txt`

If you need to re-run the copy step (idempotent) after editing the mapping:
```bash
# from workspace root
python scripts/perform_split.py
```

## 2) Repositories and structure

- Core (public):
  - Location: `repos/fba-bench-core`
  - Packaging: `repos/fba-bench-core/pyproject.toml`
  - CI: `repos/fba-bench-core/.github/workflows/ci.yml`
  - Golden masters: `repos/fba-bench-core/golden_masters/`
  - Docs (subset): `repos/fba-bench-core/docs/`

- Enterprise (private):
  - Location: `repos/fba-bench-enterprise`
  - Packaging skeleton: `repos/fba-bench-enterprise/pyproject.toml`
  - Local dependency on Core: `repos/fba-bench-enterprise/requirements.txt` (contains `-e ../fba-bench-core`)
  - CI: `repos/fba-bench-enterprise/.github/workflows/ci.yml`
  - Infra & docker: docker-compose files and Dockerfiles reside in enterprise

## 3) Local development flows

Create a virtual environment (Windows PowerShell vs. bash shown):

```bash
# Windows PowerShell
python -m venv .venv
.\\.venv\\Scripts\\Activate.ps1

# macOS/Linux
python3 -m venv .venv
source .venv/bin/activate
```

Install Core (editable) and Enterprise:

```bash
# Option A: Install via Enterprise requirements (installs Core as -e ../fba-bench-core)
pip install -r repos/fba-bench-enterprise/requirements.txt

# Option B: Install Core and Enterprise explicitly
pip install -e repos/fba-bench-core
pip install -e repos/fba-bench-enterprise
```

Smoke import checks:

```bash
# Core marker and top-level modules
python -c "import metrics, agents, baseline_bots, fba_bench_core; print('core-ok')"

# Enterprise-side smoke imports (validates Core is reachable from Enterprise env)
python -c "import runpy; runpy.run_path('repos/fba-bench-enterprise/scripts/smoke_core_imports.py')"
```

## 4) Running tests locally

Core unit tests and golden master JSON validation (from workspace root):

```bash
# Install core dev toolchain for tests
pip install -e repos/fba-bench-core pytest

# Run pytest for core
cd repos/fba-bench-core
pytest -q
cd ../..

# Golden masters lightweight JSON parse check (same as CI)
python - <<'PY'
import os, json, glob, sys
gm_dir = os.path.join('repos', 'fba-bench-core', 'golden_masters')
if os.path.isdir(gm_dir):
    fail = False
    for p in glob.glob(os.path.join(gm_dir, '**', '*.json'), recursive=True):
        try:
            json.load(open(p, 'r', encoding='utf-8'))
            print("[OK]", p)
        except Exception as e:
            print("[FAIL]", p, e)
            fail = True
    sys.exit(1 if fail else 0)
else:
    print("golden_masters/ not found; skipping")
    sys.exit(0)
PY
```

Enterprise tests (integration-oriented), if/when added under `repos/fba-bench-enterprise/tests`:

```bash
pip install -r repos/fba-bench-enterprise/requirements.txt
pip install -e repos/fba-bench-enterprise pytest

# Prefer integration marker; fallback to all tests
pytest -m integration -v repos/fba-bench-enterprise/tests || pytest -q repos/fba-bench-enterprise/tests
```

## 5) Docker and infrastructure (Enterprise)

Compose files and Dockerfiles have been routed to Enterprise. From the workspace root:

```bash
# Bring up the stack (adjust file/targets as needed)
docker compose -f repos/fba-bench-enterprise/docker-compose.yml up -d

# Tear down
docker compose -f repos/fba-bench-enterprise/docker-compose.yml down
```

If multiple compose variants exist (e.g., `docker-compose.dev.yml`, `docker-compose.prod.yml`), select the appropriate file.

## 6) CI expectations

- Core CI: `repos/fba-bench-core/.github/workflows/ci.yml`
  - Lint (ruff), type-check (mypy non-fatal), pytest, and golden master JSON validation.
- Enterprise CI: `repos/fba-bench-enterprise/.github/workflows/ci.yml`
  - Installs Core via local path (requirements.txt), installs Enterprise, and runs integration tests if present.

Local dry-run steps are embedded at the top of each workflow as comments.

## 7) Preparing to push the staged repos

Initialize Git and push the two staged repos independently. Replace placeholders (ORG/REPO) and branch as needed.

Core:

```bash
cd repos/fba-bench-core
git init
git add -A
git commit -m "feat(core): initial public core split (Phase 1)"
# Optional: set default branch
git branch -M main
git remote add origin https://github.com/ORG/fba-bench-core.git
git push -u origin main
cd ../..
```

Enterprise:

```bash
cd repos/fba-bench-enterprise
git init
git add -A
git commit -m "feat(enterprise): initial private enterprise split (Phase 1)"
git branch -M main
git remote add origin https://github.com/ORG/fba-bench-enterprise.git
git push -u origin main
cd ../..
```

## 8) Known limitations and items for review

- See `repos/PENDING_REVIEW.txt` for entries flagged during mapping (e.g., packages requiring curation for public/private boundaries).
- Tests that span both public and private components are currently scoped to Enterprise. Where possible, consider factoring shared logic into Core and retaining app/infra specifics in Enterprise.
- Legal review is required for the final license texts in both repos.

## 9) Troubleshooting

- If imports fail in Enterprise after installing requirements, ensure Core is installed in editable mode:
  ```bash
  pip install -e repos/fba-bench-core
  python -c "import metrics, agents, baseline_bots, fba_bench_core; print('core-ok')"
  ```
- If file copies look incomplete, re-run the split script (idempotent):
  ```bash
  python scripts/perform_split.py
  ```
- Verify mapping and outcomes:
  - Mapping: `repos/file_split_map.json`
  - Report: `repos/split_report.json`

## 10) Contact and next steps

- Core public README and site are staged:
  - `repos/fba-bench-core/README.md`
  - `repos/fba-bench-core/site/index.html`
- After legal and security review, proceed with pushing Core public and Enterprise private repos using the steps above.