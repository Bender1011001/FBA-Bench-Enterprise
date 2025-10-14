# FBA-Bench User Guide

This guide covers day-to-day usage of FBA-Bench for running benchmarks, managing experiments, viewing results, and configuring agents. It assumes basic setup from [docs/getting-started.md](../getting-started.md). For API details: [docs/API.md](API.md).

## Running Benchmarks

Benchmarks evaluate agents in simulations. Use CLI for quick runs or API for integration.

### CLI

1. **Simple Benchmark**:
   ```bash
   poetry run python scripts/run_benchmark_simple.py \
     --config configs/model_params.yaml \
     --scenario basic \
     --agent baseline-gpt-4o-mini
   ```
   - Loads agent/scenario from YAML.
   - Runs simulation; outputs metrics to console and `results/`.
   - Expected: ~30s runtime; logs: "Benchmark completed: score=0.85".

2. **Advanced** (multiple agents, parallel):
   ```bash
   poetry run fba-bench run \
     --config configs/benchmark_gemini_flash.yaml \
     --parallel 4 \
     --track-clearml
   ```
   - Tracks in ClearML (view at http://localhost:8080).
   - Results: JSON in `results/experiment_timestamp/summary.json`.

3. **Analyze Results**:
   ```bash
   poetry run fba-bench analyze results/experiment_timestamp/ \
     --output leaderboard.csv \
     --metrics score,roi,decisions
   ```
   - Generates CSV/HTML reports; compares agents.

CLI options: `fba-bench --help`. Configs in `configs/` (e.g., model_params.yaml for LLM params).

### API

Use curl/Postman or integrate via [services/api.ts](frontend/src/services/api.ts) in frontend.

1. **Create & Start Experiment** (see [API.md](API.md) examples):
   - POST /api/v1/experiments → get ID.
   - POST /api/v1/experiments/{id}/start with participants.

2. **Monitor**: GET /api/v1/experiments/{id}/status (poll every 5s).

3. **Benchmark Suite**: POST /benchmarks with config → POST /{id}/run.

## Viewing Dashboard

Access: http://localhost:5173 (Vite dev server).

### Navigation

- **Header**: Logo, user menu (login if auth enabled), search bar.
- **Sidebar** (Navigation.tsx):
  - Dashboard: Overview metrics (active runs, avg score).
  - Experiments: List/create runs; filter by status/agent.
  - Leaderboard: Agent rankings (table/charts via Recharts/ECharts).
  - Settings: Config agents, scenarios, API keys.

- **Pages** (React Router):
  - **Dashboard** (Dashboard.tsx): Real-time cards (running experiments, recent scores, system health from Prometheus).
  - **Experiments** (Experiments.tsx): Table of runs; buttons: Start, Stop, View Results. Search/filter.
  - **Leaderboard** (Leaderboard.tsx): Sorted table (agent, score, ROI, decisions); charts (bar/line for metrics).
  - **Settings** (Settings.tsx): Forms for model_params.yaml upload, agent validation, theme (dark mode).

Use LoadingSpinner for async loads; error boundaries show user-friendly messages.

## Interpreting Results

Results stored in Postgres/ClearML; view in dashboard or `results/`.

### Key Metrics

- **Overall Score**: Composite (0-1); higher better (balances financial, decision quality).
- **Financial KPIs**:
  - ROI: Return on Investment (%).
  - Profit: Net profit from simulation ($).
  - Risk Score: Volatility measure (lower better).
- **Agent Performance**:
  - Decisions Made: Actions taken (higher for complex scenarios).
  - Latency: Avg response time (ms).
  - Success Rate: % optimal decisions.
- **Simulation**:
  - Ticks: Completed/total steps.
  - Events Handled: Processed events (supply disruptions, etc.).

Example summary.json:
```json
{
  "experiment_id": "uuid",
  "overall_score": 0.85,
  "financial": {"roi": 15.2, "profit": 1250.0},
  "agent_metrics": {"decisions": 45, "success_rate": 92.0},
  "duration_seconds": 30.5
}
```

Leaderboard: Compares agents (e.g., GPT-4o vs. Claude); export CSV.

Interpret: High score = robust agent; low ROI = poor financial strategy. Use ClearML for hyperparam sweeps.

## Configuring Agents

Agents defined in YAML; baseline bots in baseline_bots/.

1. **Edit Config** (model_params.yaml):
   ```yaml
   agents:
     - name: my-gpt-agent
       framework: baseline
       llm_config:
         model: gpt-4o-mini
         temperature: 0.2
         api_key: ${OPENAI_API_KEY}
       skills: [financial_analyst, supply_manager]
   scenarios:
     basic:
       duration: 100  # ticks
       events: [supply_disruption]
   ```
   - Frameworks: baseline (simple), crewai (teams), langchain (ReAct).

2. **Validate**:
   - CLI: `poetry run python -c "from benchmarking.config import UnifiedAgentRunnerConfig; cfg = UnifiedAgentRunnerConfig.from_yaml('config.yaml'); print('Valid')"`
   - API: POST /api/v1/agents/validate with {"agent_config": yaml_dump}.

3. **Custom Skills**: Extend src/agents/skill_modules/base_skill.py; register in agent_factory.

Upload via Settings page; test in simple run.

## Tutorial: Running Your First FBA Benchmark

1. **Setup**: Follow getting-started; ensure .env has OPENAI_API_KEY.

2. **Create Experiment** (Dashboard or CLI):
   - Dashboard: Experiments → New → Name: "First-Bench", Agent: baseline-gpt-4o-mini, Scenario: basic → Create.
   - CLI: `poetry run python scripts/create_experiment.py --name "First-Bench" --agent baseline-gpt-4o-mini`

3. **Start Run**:
   - Dashboard: Experiments → Select → Start (auto-adds participant).
   - CLI: `poetry run python scripts/start_run.py --exp-id {id} --scenario basic`
   - Or API: See examples above.

4. **Monitor**:
   - Dashboard: Progress bar (45% at tick 45/100); real-time updates via WebSockets.
   - Expected: 30-60s; status: pending → starting → running → completed.
   - If error: "API key invalid" → check .env.

5. **View Results**:
   - Dashboard: Leaderboard → See "First-Bench" row: score ~0.8, ROI 12%.
   - CLI: `cat results/first-bench/summary.json`
   - Screenshot Description: Table with columns Agent, Score, Profit; bar chart for ROI comparison. Green success indicator.

6. **Interpret & Iterate**:
   - Low score? Increase temperature or add skills.
   - Rerun: Experiments → Duplicate → Start.

Expected Output (console):
```
Benchmark started: exp-uuid
Tick 50/100: progress 50%
Completed: score=0.82, profit=$1150
View in ClearML: http://localhost:8080/projects/...
```

## Error Handling

Frontend uses error boundaries (React); API returns structured errors. Common issues:

| Error | Cause | User Message | Resolution |
|-------|-------|--------------|------------|
| "Validation Error: name required" | Missing field in create | "Please provide a name for your experiment." | Fill required fields; validate YAML. |
| "Rate limit exceeded - try again in 1 min" | Too many requests | "Slow down; wait 60s before retrying." | Check X-RateLimit-Remaining; use longer intervals. |
| "Agent not found" | Invalid agent_id | "Selected agent doesn't exist. Check ID." | List via /agents/available; create if needed. |
| "API key invalid" | Wrong key in .env | "Authentication failed. Verify your API key." | Regenerate key; restart services. |
| "Database connection failed" | DB down | "Service unavailable. Check database." | Start Postgres: docker compose up db; migrate. |
| "Simulation timeout" | Long run | "Run exceeded time limit." | Increase iterations or check resources (RAM/CPU). |

Logs: Check API console or ClearML. Frontend: toast notifications (react-hot-toast) for UX.

## Onboarding and UX Improvements

### Guided Tour

On first login (GuidedTour.tsx), a 4-step tour (Framer Motion animations):

1. **Welcome**: "Welcome to FBA-Bench! Overview of dashboard."
2. **Experiments**: "Create and manage your benchmarks here."
3. **Leaderboard**: "Compare agent performance."
4. **Settings**: "Configure agents and API keys."

Tour skips if dismissed; re-trigger via Settings.

### Suggested Improvements

- **Tooltips**: Add Lucide icons with hover tips (e.g., "Click to start run" on buttons).
- **Help Modals**: Context-sensitive (e.g., ? icon → modal with metric explanations).
- **Onboarding Flow**: Wizard in Settings for first config (API key → agent setup → first run).
- **Accessibility**: ARIA labels on charts; keyboard nav for tables.
- **Error UX**: Inline validation (red borders); retry buttons for network errors.

Reference: frontend/src/components/tour/GuidedTour.tsx. Contribute UX fixes via PRs.

For advanced usage: [docs/contributing.md](../CONTRIBUTING.md). Questions? GitHub issues.