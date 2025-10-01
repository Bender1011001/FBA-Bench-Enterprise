import { RuntimeConfig, SettingsPayload, SettingsResponse } from 'types/api';
import { getApiBaseUrl } from './config';

type ErrorBody = { error?: string } | null | undefined;

/**
 * SettingsService - Runtime config and UI settings using Phase 1 endpoints.
 * Base URL follows config.ts: getApiBaseUrl() with same-origin default for production safety.
 */

const API_BASE_URL: string = getApiBaseUrl();


class SettingsAPIError extends Error {
  constructor(public status: number, public body: unknown, message?: string) {
    const b = body as ErrorBody;
    super(message || (b?.error ?? `HTTP ${status}`));
    this.name = 'SettingsAPIError';
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
      throw new SettingsAPIError(res.status, data, data?.error || res.statusText);
    }
    return data as T;
  } catch (err: unknown) {
    if (err instanceof SettingsAPIError) throw err;
    const message = err instanceof Error ? err.message : 'Unknown error';
    throw new SettingsAPIError(0, null, `Network error: ${message}`);
  }
}

// UI settings - GET /api/v1/settings
export async function getSettings(): Promise<SettingsResponse> {
  return request<SettingsResponse>('/api/v1/settings', { method: 'GET' });
}

// UI settings - POST /api/v1/settings
export async function postSettings(payload: SettingsPayload): Promise<SettingsResponse> {
  return request<SettingsResponse>('/api/v1/settings', {
    method: 'POST',
    body: JSON.stringify(payload ?? {}),
  });
}

// Runtime config - GET /api/v1/config
export async function getRuntimeConfig(): Promise<RuntimeConfig> {
  return request<RuntimeConfig>('/api/v1/config', { method: 'GET' });
}

// Runtime config - PATCH /api/v1/config
export async function patchRuntimeConfig(patch: RuntimeConfig): Promise<RuntimeConfig> {
  return request<RuntimeConfig>('/api/v1/config', {
    method: 'PATCH',
    body: JSON.stringify(patch ?? {}),
  });
}

export function isSettingsAPIError(e: unknown): e is SettingsAPIError {
  return e instanceof SettingsAPIError;
}
