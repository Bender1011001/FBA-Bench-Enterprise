# Project Medusa: Canonical Documentation

Overview
- Medusa automates iterative benchmarking and evolution of agent configurations (“genomes”).
- Core modules: [medusa_trainer.py](../medusa_experiments/medusa_trainer.py), [medusa_analyzer.py](../medusa_experiments/medusa_analyzer.py), [schema.py](../medusa_experiments/schema.py)

Directory Structure
- Core: [medusa_experiments](../medusa_experiments)
  - Trainer: [medusa_trainer.py](../medusa_experiments/medusa_trainer.py)
  - Analyzer: [medusa_analyzer.py](../medusa_experiments/medusa_analyzer.py)
  - Schema: [schema.py](../medusa_experiments/schema.py)
  - Genomes: [genomes](../medusa_experiments/genomes) (create if missing)
  - Logs: [logs](../medusa_experiments/logs) (create if missing)
- Results: [medusa_results](../medusa_results)
- Backend API: [medusa router](../src/fba_bench_api/api/routers/medusa.py)
- Frontend (canonical): [MedusaDashboard.tsx](../repos/fba-bench-enterprise/frontend/src/pages/medusa/MedusaDashboard.tsx), [medusa.ts](../repos/fba-bench-enterprise/frontend/src/api/medusa.ts)

API Endpoints (typical)
- POST /api/v1/medusa/start
- POST /api/v1/medusa/stop
- GET /api/v1/medusa/status
- GET /api/v1/medusa/logs
- GET /api/v1/medusa/analysis

Quick Start
1. `poetry run fba run full`
2. Open http://localhost:80/medusa
3. Ensure directories exist: [logs](../medusa_experiments/logs), [genomes](../medusa_experiments/genomes), [medusa_results](../medusa_results)

Testing
- Backend: [test_medusa.py](../tests/api/test_medusa.py)
- Frontend: [medusa_tests.tsx](../tests/frontend/medusa_tests.tsx)

Notes
- If logs directory does not exist, it will be created on first run. Otherwise, create manually:
  - Windows: `mkdir medusa_experiments\\logs && mkdir medusa_experiments\\genomes`
  - Unix: `mkdir -p medusa_experiments/logs medusa_experiments/genomes`