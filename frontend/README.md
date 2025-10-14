# FBA-Bench Frontend

This is the React/TypeScript frontend for the FBA-Bench dashboard, built with Vite, Tailwind CSS, and Zustand for state management. It provides a professional interface for simulation analysis, experiments, leaderboards, and settings.

## Setup and Development

1. **Install Dependencies:**
   ```bash
   cd frontend
   npm install
   ```

2. **Run Development Server:**
   ```bash
   npm run dev
   ```
   The app will be available at `http://localhost:5173` (Vite default).

3. **Build for Production:**
   ```bash
   npm run build
   ```
   Outputs to `dist/` directory.

4. **Run Tests:**
   ```bash
   npm run test
   ```

5. **Lint and Format:**
   ```bash
   npm run lint
   npm run lint:fix
   ```

## Key Features
- **Dashboard:** Real-time simulation metrics and visualizations (ECharts, Recharts).
- **Experiments:** Manage and run FBA-Bench scenarios.
- **Leaderboard:** Track agent performance.
- **Medusa Logs:** View training and inference logs.
- **Settings:** Configure environment, API endpoints, and themes.
- **Guided Tour:** Interactive onboarding with react-joyride.

## API Integration
The frontend connects to the backend API at `http://localhost:8000` (configurable). See the [Frontend Auth API Client](../repos/fba-bench-enterprise/README.md#frontend-auth-api-client) section in the enterprise README for authentication details.

### Auth API Client
- Types: [src/types/auth.ts](src/types/auth.ts)
- Token Storage: [src/auth/tokenStorage.ts](src/auth/tokenStorage.ts)
- HTTP Wrapper: [src/api/http.ts](src/api/http.ts)
- Auth Functions: [src/api/auth.ts](src/api/auth.ts)

Usage examples and configuration are documented in the enterprise README.

## Environment Variables
- `VITE_API_BASE_URL`: Override default API base URL (e.g., for production).
- See `.env.example` for other configs.

## Project Structure
- `src/components/`: Reusable UI components (e.g., LoadingSpinner, Header).
- `src/pages/`: Route-based pages (Dashboard, Experiments).
- `src/services/`: API clients and utilities (e.g., clearml.ts for experiment tracking).
- `src/store/`: Zustand stores for global state.
- `src/types/`: TypeScript interfaces (e.g., api.ts, auth.ts).

## Notes
- Uses TypeScript strict mode; ensure no type errors with `npx tsc --noEmit`.
- Tailwind CSS for styling; extend in `tailwind.config.js`.
- For production, build and serve via Nginx or integrate with backend.

For backend setup, see [../repos/fba-bench-enterprise/README.md](../repos/fba-bench-enterprise/README.md).