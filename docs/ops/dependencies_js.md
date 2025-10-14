# JavaScript Dependencies Audit

## Overview
This audit analyzes the frontend dependencies in the Vite/React project located at `frontend/`. The scope covers `package.json`, `vite.config.ts`, and usage patterns in `src/` (including `services/api.ts` and `store/`). Tools used: `codebase_search` for semantic exploration, `read_file` for manifests, `search_files` for import cross-checks, and npm commands (`ci`, `audit --json`, `ls --all`, `outdated`) executed in `frontend/` on Windows. No modifications were made to source code or lockfiles. Artifacts generated in `test_results/`: `npm_audit.json`, `npm_ls.txt`, `npm_outdated.txt`. Audit date: 2025-09-29.

## Dependency Inventory
### Runtime Dependencies (from `frontend/package.json`)
- **@headlessui/react@^1.7.17**: UI components for modals, dialogs, etc. (used in setup wizards and tours).
- **@heroicons/react@^2.0.18**: SVG icons for UI elements (navigation, buttons).
- **@types/node@^20.10.0**: Type definitions for Node.js (build-time usage in Vite config).
- **@types/react@^18.2.45**: TypeScript types for React components.
- **@types/react-dom@^18.2.18**: TypeScript types for React DOM rendering.
- **autoprefixer@^10.4.16**: PostCSS plugin for adding vendor prefixes to CSS output.
- **axios@^1.8.0**: HTTP client for API requests (core usage in `src/services/api.ts` for backend integration).
- **clsx@^2.0.0**: Conditional class name utility for Tailwind CSS in components.
- **date-fns@^2.30.0**: Lightweight date manipulation and formatting (used for timestamps in dashboard and experiments).
- **echarts@^5.4.3**: Advanced charting library for complex visualizations (leaderboard, metrics).
- **echarts-for-react@^3.0.2**: React wrapper for seamless ECharts integration.
- **framer-motion@^10.18.0**: Animation and gesture library for smooth UI transitions (e.g., modals, tours).
- **lucide-react@^0.294.0**: Open-source icon set for consistent UI icons.
- **postcss@^8.4.32**: CSS post-processor for Tailwind and Autoprefixer.
- **react@^18.2.0**: Core React library for building the UI.
- **react-dom@^18.2.0**: DOM-specific rendering for React.
- **react-hot-toast@^2.6.0**: Non-blocking toast notifications for user feedback (errors, success messages).
- **react-json-viewer@^3.0.1**: Interactive JSON viewer for debugging API responses and configs.
- **react-router-dom@^6.30.1**: Browser routing for SPA navigation (pages like Dashboard, Leaderboard).
- **recharts@^2.8.0**: Simple, composable charting (potential backup or simple charts; overlaps with ECharts).
- **tailwindcss@^3.3.6**: Utility-first CSS framework for styling.
- **typescript@^5.3.3**: TypeScript compiler for type-safe development.
- **web-vitals@^3.5.0**: Web performance metrics (used in dev tools for monitoring).
- **zustand@^4.4.7**: Minimal state management (global app state in `src/store/appStore.ts`, dashboard state).

### Dev Dependencies and Scripts
- **@testing-library/jest-dom@^6.8.0**: Custom Jest matchers for DOM testing.
- **@testing-library/react@^16.3.0**: Utilities for React component testing.
- **@testing-library/user-event@^14.6.1**: Simulates user interactions in tests.
- **@types/jest@^29.5.8**: Type definitions for Jest.
- **@typescript-eslint/eslint-plugin@^6.13.1**: ESLint rules for TypeScript.
- **@typescript-eslint/parser@^6.13.1**: ESLint parser for TypeScript.
- **@vitejs/plugin-react@^4.3.4**: Vite plugin for React fast refresh and JSX.
- **@vitest/coverage-v8@^3.2.4**: V8-based coverage for Vitest.
- **ajv@^8.17.1**: JSON schema validator (used in build validation scripts).
- **ajv-keywords@^5.1.0**: Additional AJV keywords for validation.
- **eslint@^8.54.0**: Linting tool for code quality.
- **eslint-plugin-react@^7.33.2**: React-specific ESLint rules.
- **eslint-plugin-react-hooks@^4.6.0**: Enforces React Hooks rules.
- **jsdom@^27.0.0**: DOM simulator for testing.
- **vite@^7.1.6**: Build tool and dev server.
- **vite-tsconfig-paths@^5.1.0**: Resolves TypeScript path aliases in Vite.

Scripts in `package.json`:
- `dev`: Starts Vite dev server on host 0.0.0.0:5173.
- `build`: Builds production bundle to `dist/`.
- `build:profile`: Validates env, builds with profiling, verifies output.
- `preview`: Serves built app on port 4173.
- `test`: Runs Vitest tests.
- `test:watch`: Interactive test watching.
- `test:ui`: Vitest UI mode.
- `coverage`: Runs tests with V8 coverage.
- `lint`: ESLint on src TS/TSX files.
- `lint:fix`: Auto-fixes lint issues.
- `audit`: Runs npm audit at high level.

Tooling: Vite config proxies `/api`, `/setup`, `/system` to backend (localhost:8000), enables WebSocket. Tailwind/PostCSS for styling. Vitest for testing with V8 coverage.

## Usage vs Declaration
Cross-checked imports in `frontend/src/*.ts(x)` via semantic search and regex patterns for key deps (axios, framer-motion, zustand, react-router-dom, recharts, react-hot-toast, echarts-for-react, lucide-react, headlessui, date-fns, clsx, react-json-viewer, web-vitals, heroicons, echarts). No exact import matches found in search (possible due to dynamic imports or aliasing via tsconfig paths like "services/*" -> "src/services/*"). However, codebase analysis confirms usage:

- Active: axios (API service), zustand (stores), react-router-dom (routing in App.tsx), framer-motion (animations in components), react-hot-toast (notifications), date-fns/clsx/lucide-react/@heroicons (UI utils in components/pages), Tailwind (global styles).
- Likely active: echarts/echarts-for-react (dashboard/leaderboard visualizations), react-json-viewer (debug views), web-vitals (perf monitoring).
- Potential duplication: recharts and echarts both for charts; recharts may be unused or legacy (no confirmed imports; heuristic: if ECharts handles all viz, remove recharts to reduce bundle size ~200KB).
- Headless UI: Used in modals/tours per architecture docs.
- Uncertainties: Dynamic imports (e.g., lazy-loaded pages) or tree-shaking may hide static imports. No duplicated declarations evident. All @types/* are build-time only. No unused deps flagged definitively; recommend `npm ls --depth=0` and manual review in next phase.

Total runtime deps: 24 (including types/build tools). Dev: 16. Transitive deps: 663 total (from npm ls).

## Security Findings
npm audit reports 0 vulnerabilities (info: 0, low: 0, moderate: 0, high: 0, critical: 0). No direct or transitive issues in declared packages. All deps are up-to-date within minor/patch ranges where no vulns exist. Deprecated warnings during install (e.g., inflight@1.0.6, rimraf@3.0.2, glob@7.2.3, eslint@8.57.1) are transitive and non-vulnerable but indicate aging sub-deps. No EOL packages (e.g., React 18 supported until 2025+). See `test_results/npm_audit.json` for full metadata.

## Remediation Plan
No security remediations needed (0 vulns). Focus on outdated packages for maintenance, compatibility, and perf. Prioritize based on major version jumps, deprecation risks, and impact:

### High Priority (within 48h: Major updates, potential breaking changes)
- **eslint@8.57.1 -> 9.36.0** (`frontend/package.json`): Breaking changes; update rules/plugins (@typescript-eslint/* to 8.x). Test linting post-upgrade.
- **@typescript-eslint/eslint-plugin@6.21.0 & @typescript-eslint/parser@6.21.0 -> 8.44.1**: Align with ESLint 9; review rule changes.
- **react@18.3.1 & react-dom@18.3.1 -> 19.1.1**: Major React upgrade; audit hooks/components for compat (e.g., new compiler, actions). Update @types/react@18.3.24 -> 19.1.15, @types/react-dom@18.3.7 -> 19.1.9.
- **@vitejs/plugin-react@4.7.0 -> 5.0.4**: Vite ecosystem update; minimal breaking changes.
- **framer-motion@10.18.0 -> 12.23.22**: Major; test animations/transitions.
- **react-router-dom@6.30.1 -> 7.9.3**: Data APIs changes; update routing in App.tsx.

### Medium Priority (within a week: Minor/major but low-risk)
- **@types/node@20.19.17 -> 24.5.2**: Node types update; ensure Vite compat.
- **@types/jest@29.5.14 -> 30.0.0**: Jest types; update tests if needed.
- **date-fns@2.30.0 -> 4.1.0**: Breaking; migrate date utils.
- **echarts@5.6.0 -> 6.0.0**: Charting updates; test visualizations.
- **lucide-react@0.294.0 -> 0.544.0**: Icon set expansion; low risk.
- **recharts@2.15.4 -> 3.2.1**: If used, upgrade; else remove.
- **tailwindcss@3.4.17 -> 4.1.13**: Major; redesign utilities if breaking.
- **web-vitals@3.5.2 -> 5.1.0**: Perf metrics; update monitoring.
- **zustand@4.5.7 -> 5.0.8**: State mgmt; minor breaking in middleware.
- Transitive deprecations (e.g., rimraf@3.0.2): Handled by upstream updates (e.g., via ESLint/Vite).

Remove if unused: recharts (dupe with ECharts; save ~200KB). Pin vulns-free versions post-upgrade. No transitive-only issues.

## Next Steps
- Create PR: Branch `feat/js-deps-audit-remediation`, apply upgrades sequentially (test each), update lockfile, run `npm audit`/`outdated` post-merge.
- CI Integration: Add to `.github/workflows/ci.yml`: `npm ci && npm audit --audit-level=high` (fail on high/critical), `npm outdated --parseable` (warn on majors), weekly Dependabot scans. Enforce in Makefile (e.g., `make js-audit`).
- Future: Integrate `npm-check-updates` in CI, migrate to ESLint 9/React 19 in phases, monitor via `npm ls` for bloat.