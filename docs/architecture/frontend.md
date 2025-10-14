# Frontend Architecture

## Overview
The frontend is a React-based dashboard built with Vite, serving as the user interface for the FBA-Bench simulation platform. It provides visualization, management, and monitoring of experiments, leaderboards, and system metrics. The dashboard interacts with the backend API for data retrieval and control operations, with real-time updates via WebSocket. Key boundaries include API proxying through Vite for development and environment-specific configuration via Vite env variables. The application emphasizes a professional, responsive UI with guided onboarding and error handling at the root level.

## Structure and Routing
The component hierarchy is organized under [frontend/src/components/](frontend/src/components/) and [frontend/src/pages/](frontend/src/pages/), with routing defined inline in [frontend/src/App.tsx](frontend/src/App.tsx) using react-router-dom. No dedicated router directory exists.

- **Top-level Components (Level 1)**:
  - App: Root component handling initialization, status checks, modals (ConfigurationWizard, EnvironmentSetupModal, GuidedTour), and ErrorBoundary.
  - Router (BrowserRouter): Wraps the application, containing Navigation (layout) and Routes.
  - ErrorBoundary: Catches and displays generic errors at the app level.

- **Layout and Cross-cutting (Level 2)**:
  - Navigation: Sidebar with links to pages, connection status indicators.
  - LoadingScreen: Initial loading and error states.
  - Toaster: Global notifications via react-hot-toast.

- **Page-level Routes (Level 3)**:
  - /dashboard → Dashboard (metrics, recent activity).
  - /experiments → Experiments (list, create, manage simulations).
  - /templates → Templates (pre-built scenarios).
  - /leaderboard → Leaderboard (rankings, comparisons).
  - /medusa → MedusaDashboard (Medusa-specific views).
  - /settings → Settings (configuration, API keys).
  - /medusa-logs → MedusaLogs (log viewer).
  - * (wildcard) → Redirect to /dashboard.

Cross-cutting: Header and Navigation provide consistent layout; LoadingSpinner used in async components. No explicit dynamic routes (e.g., /experiments/:id). Code-splitting not implemented; all routes load eagerly.

## State Management (Zustand)
State is managed via two Zustand stores in [frontend/src/store/](frontend/src/store/): appStore.ts for global application state and dashboardStore.ts for dashboard-specific data. subscribeWithSelector middleware enables efficient subscriptions. No persist or immer middleware; state is in-memory with localStorage for flags (e.g., tour completion, wizard skip).

- **appStore.ts Responsibilities**:
  - Global: Connection status (API, ClearML, WS), experiments list, system stats, leaderboard, notifications, filters (status, project, search).
  - UI: Selected experiment, sidebar collapse, theme.
  - Loading: Per-resource flags (experiments, stats, leaderboard).
  - Patterns: Selectors for performance (e.g., useExperiments). Actions for updates, notifications (capped at 50), filters. Shared across all pages; risks over-sharing (e.g., experiments loaded globally but used per-page).

- **dashboardStore.ts Responsibilities**:
  - Dashboard-specific: Async states for executive summary, financial deep dive, product market analysis, supply chain operations, agent cognition, KPI metrics.
  - UI: Active tab, loading/error for tabs.
  - Filters: Time range (default 7 days), event types, agent-only toggle.
  - Real-time: WS event handling (e.g., KPI updates, simulation refresh).
  - Patterns: AsyncState wrapper (data/loading/error/lastUpdated). Selectors for data access. Per-page usage (tied to Dashboard page); boundaries clear but could leak if WS events update global appStore indirectly.

Risks: Tight coupling (stores directly update from API/WS without abstraction); missing types in some actions; potential concurrency (multiple tabs refreshing data); over-shared global state in appStore may cause unnecessary re-renders without memoization.

## API Layer
API interactions are centralized in [frontend/src/services/api.ts](frontend/src/services/api.ts) using axios, with adjacent services for ClearML ([frontend/src/services/clearml.ts](frontend/src/services/clearml.ts)), config, environment, simulation, and stack management. No other major service modules noted.

- **Structure**: Axios instance with baseURL from import.meta.env.VITE_API_URL (default localhost:8000). Methods (get/post/put/delete) return ApiResponse<T> with typed data/status. Endpoints: /health, /api/v1/experiments, /api/v1/leaderboard, /system/stats, /setup/env-check, /api/v1/stack/clearml/*, /api/v1/medusa/logs.
- **Error Handling**: Global response interceptor shows toasts for 401 (session expired) and 500+ (server error). Per-method try-catch logs details and toasts generic failures. Health check handles 503 (backend startup) with retry hint. No systematic retry/backoff (e.g., exponential); manual in some cases (e.g., WS reconnect not implemented).
- **Auth/Token Handling**: No explicit token management; assumes backend handles auth. 401 triggers refresh toast. API key testing (OpenAI, OpenRouter, ClearML) via direct fetch to external endpoints, stored in environmentService (localStorage).
- **Env/Config**: Vite envs resolve base URLs (VITE_API_URL, VITE_WS_URL). Proxy in vite.config.ts routes /api, /setup, /system, /ws to backend. WS connection/subscribe in api.ts for real-time (e.g., kpi_update, simulation_update).

## Build and Tooling
- **Scripts ([frontend/package.json](frontend/package.json))**:
  - dev: vite --host 0.0.0.0 (port 5173).
  - build: vite build (outDir: dist, no sourcemap).
  - build:profile: Validates env, builds with --profile, verifies output.
  - preview: vite preview (port 4173).
  - test: vitest --run; test:watch, test:ui for interactive.
  - coverage: vitest run --coverage (v8 provider, reporters: text/json/html).
  - lint: eslint src --ext .ts,.tsx; lint:fix applies fixes.
  - audit: npm audit --audit-level=high.
  - Key Deps: react^18.2.0, react-router-dom^6.30.1, zustand^4.4.7, axios^1.8.0, framer-motion^10.18.0, recharts^2.8.0, react-hot-toast^2.6.0.

- **Vite Config ([frontend/vite.config.ts](frontend/vite.config.ts))**:
  - Plugins: @vitejs/plugin-react, vite-tsconfig-paths (aliases from tsconfig).
  - Server: Host 0.0.0.0:5173, proxies /api /setup /system to VITE_API_URL (default localhost:8000), /ws to ws://localhost:8000 (WebSocket support).
  - Build: outDir dist, assetsInlineLimit 4096B, cssCodeSplit false, no manualChunks (single bundle).
  - Preview: Port 4173.

- **Testing ([frontend/vitest.config.ts](frontend/vitest.config.ts))**:
  - Environment: jsdom, setup: src/test/setupTests.ts, no globals.
  - Include: tests/frontend/**/*.test.tsx, etc. (suggests tests/ dir, but not in file list).
  - Coverage: v8 provider, include src/**/*.{ts,tsx}, exclude d.ts/main.tsx/etc., thresholds 100% (lines/functions/branches/statements). Reporters: text/json/html.

## Gaps and Risks
- **Missing Error Boundaries**: Only root-level ErrorBoundary; page-specific errors (e.g., in Dashboard) could crash UI. Risk: Poor UX on component failures. Mitigation: Add per-page boundaries.
- **Inconsistent API Usage**: Direct axios in api.ts with manual normalization (e.g., experiments); no unified response typing across services. Risk: Untyped responses lead to runtime errors. Mitigation: Enforce ApiResponse<T> everywhere, add Zod for validation.
- **No Retry/Backoff**: API lacks automatic retries for transient failures (e.g., network). Risk: Flaky connections during dev/testing. Mitigation: Add axios-retry interceptor.
- **Over-shared State**: appStore holds global experiments/leaderboard, potentially causing re-renders across unrelated pages. Risk: Performance degradation with large datasets. Mitigation: Lazy-load per-page, use immer for immutable updates.
- **Testing Gaps**: Coverage targets 100% but include patterns reference missing tests/frontend/ dir; no integration/e2e tests noted. Risk: Low actual coverage, undetected regressions. Mitigation: Create tests/frontend/, add @testing-library/react suites for components/stores.
- **No Code-Splitting**: Eager loading of all routes/components. Risk: Slow initial load for large app. Mitigation: Implement React.lazy for pages.
- **State Leaks**: WS events in dashboardStore could update stale data without cleanup. Risk: Inconsistent views on navigation. Mitigation: Add store subscriptions with unmount cleanup.

## Next Steps
- **Tests**: Add unit tests for stores (e.g., appStore normalization) and components (e.g., Navigation connection indicators) targeting 80% coverage initially; run make test-contracts equivalent via vitest. Create integration tests for API flows (e.g., experiment CRUD) in tests/integration/.
- **Coverage Targets**: Lower thresholds to 80% for CI (make ci-local), enforce via GitHub Actions; add performance benchmarks for re-renders using React DevTools profiler.
- **Typing Improvements**: Add full types for WS events and API responses; integrate TypeScript strict mode checks (make type-check). Audit untyped any in stores/services.
- **CI Checks**: Integrate lint/test/coverage into pre-commit hooks (make pre-commit-install); add build verification script to ensure no console errors in preview mode.
- **Stabilization**: Implement API retry (3 attempts, exponential backoff); add per-page error boundaries and loading skeletons for async data.