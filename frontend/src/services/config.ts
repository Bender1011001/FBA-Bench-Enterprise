/**
 * Centralized environment-aware configuration for frontend networking.
 * Supports both CRA (process.env.REACT_APP_*) and Vite (import.meta.env.VITE_*).
 * Defaults to same-origin for production safety when no env vars are provided.
 */

type ViteEnv = { [key: string]: string | undefined };

/** Safely read env from Vite or CRA */
function readEnv(viteKey: string, craKey: string): string | undefined {
  // Prefer Vite env at build time
  try {
    const viteEnv = (typeof import.meta !== 'undefined' && (import.meta as unknown as { env?: ViteEnv }).env) as ViteEnv | undefined;
    if (viteEnv && viteEnv[viteKey]) return viteEnv[viteKey];
  } catch {
    // ignore
  }
  // Fallback to CRA env
  try {
    if (typeof process !== 'undefined' && (process as unknown as { env?: Record<string, string | undefined> }).env) {
      const val = (process as unknown as { env?: Record<string, string | undefined> }).env![craKey];
      if (val) return val as string;
    }
  } catch {
    // ignore
  }
  return undefined;
}

// Return normalized API base URL (no trailing slash)
export function getApiBaseUrl(): string {
  const raw = (readEnv('VITE_API_URL', 'REACT_APP_API_URL') || '').trim();
  const base = raw || window.location.origin;
  return base.replace(/\/+$/, '');
}

// Return WebSocket URL. Uses env override or derives from current location.
export function getWebSocketUrl(): string {
  const raw = (readEnv('VITE_WS_URL', 'REACT_APP_WS_URL') || '').trim();
  if (raw) return raw;
  const isHttps = window.location.protocol === 'https:';
  const scheme = isHttps ? 'wss' : 'ws';
  return `${scheme}://${window.location.host}/ws`;
}

// Optional runtime validation; build-time validation happens in scripts/validate-env.cjs (when configured)
export function validateRuntimeEnv(): void {
  const api = (readEnv('VITE_API_URL', 'REACT_APP_API_URL') || '').trim();
  if (api && !/^https?:\/\//i.test(api)) {
    // Allow empty (same-origin), otherwise require absolute URL to avoid ambiguous bases
    // eslint-disable-next-line no-console
    console.warn('Invalid API URL. Expected absolute http(s) URL or empty for same-origin.');
  }
  const ws = (readEnv('VITE_WS_URL', 'REACT_APP_WS_URL') || '').trim();
  if (ws && !/^wss?:\/\//i.test(ws)) {
    // eslint-disable-next-line no-console
    console.warn('Invalid WS URL. Expected ws(s) URL or empty to derive from window.location.');
  }
}