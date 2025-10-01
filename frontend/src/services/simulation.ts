import { SimulationActionResponse, SimulationSnapshot, SimulationSpeedRequest } from 'types/api';
import { getApiBaseUrl } from './config';

type ErrorBody = { error?: string } | null | undefined;

/**
 * SimulationService - Orchestrator controls using Phase 1 endpoints.
 * Base URL uses config.ts getApiBaseUrl() with same-origin default for production safety.
 */

const API_BASE_URL: string = getApiBaseUrl();


class SimulationAPIError extends Error {
  constructor(public status: number, public body: unknown, message?: string) {
    const b = body as ErrorBody;
    super(message || (b?.error ?? `HTTP ${status}`));
    this.name = 'SimulationAPIError';
  }
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  const config: RequestInit = {
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    },
    ...options,
  };

  try {
    const res = await fetch(url, config);
    const text = await res.text();
    const data = text ? JSON.parse(text) : null;

    if (!res.ok) {
      throw new SimulationAPIError(res.status, data, data?.error || res.statusText);
    }
    return data as T;
  } catch (err: unknown) {
    if (err instanceof SimulationAPIError) throw err;
    const message = err instanceof Error ? err.message : 'Unknown error';
    throw new SimulationAPIError(0, null, `Network error: ${message}`);
  }
}

// POST /api/v1/simulation/start
export async function startSimulation(): Promise<SimulationActionResponse> {
  return request<SimulationActionResponse>('/api/v1/simulation/start', { method: 'POST' });
}

// POST /api/v1/simulation/stop
export async function stopSimulation(): Promise<SimulationActionResponse> {
  return request<SimulationActionResponse>('/api/v1/simulation/stop', { method: 'POST' });
}

// POST /api/v1/simulation/pause
export async function pauseSimulation(): Promise<SimulationActionResponse> {
  return request<SimulationActionResponse>('/api/v1/simulation/pause', { method: 'POST' });
}

// POST /api/v1/simulation/resume
export async function resumeSimulation(): Promise<SimulationActionResponse> {
  return request<SimulationActionResponse>('/api/v1/simulation/resume', { method: 'POST' });
}

// POST /api/v1/simulation/speed
export async function setSimulationSpeed(speed: number): Promise<SimulationActionResponse> {
  const payload: SimulationSpeedRequest = { speed };
  return request<SimulationActionResponse>('/api/v1/simulation/speed', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

// GET /api/v1/simulation/snapshot
export async function getSimulationSnapshot(): Promise<SimulationSnapshot> {
  return request<SimulationSnapshot>('/api/v1/simulation/snapshot', { method: 'GET' });
}

export function isSimulationAPIError(e: unknown): e is SimulationAPIError {
  return e instanceof SimulationAPIError;
}
