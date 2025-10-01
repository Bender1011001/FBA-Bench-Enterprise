import { ClearMLStackStartRequest, ClearMLStackStartResponse, ClearMLStackStatus } from 'types/api';
import { getApiBaseUrl } from './config';

type ErrorBody = { error?: string } | null | undefined;

/**
 * StackService - ClearML stack controls using Phase 1 endpoints.
 * Uses config.ts getApiBaseUrl() with same-origin default for production safety.
 */

const API_BASE_URL: string = getApiBaseUrl();


class StackAPIError extends Error {
  constructor(public status: number, public body: unknown, message?: string) {
    const b = body as ErrorBody;
    super(message || (b?.error ?? `HTTP ${status}`));
    this.name = 'StackAPIError';
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
      throw new StackAPIError(res.status, data, data?.error || res.statusText);
    }
    return data as T;
  } catch (err: unknown) {
    if (err instanceof StackAPIError) throw err;
    const message = err instanceof Error ? err.message : 'Unknown error';
    throw new StackAPIError(0, null, `Network error: ${message}`);
  }
}

/**
 * POST /api/v1/stack/clearml/start
 */
export async function startClearMLStack(payload?: ClearMLStackStartRequest): Promise<ClearMLStackStartResponse> {
  return request<ClearMLStackStartResponse>('/api/v1/stack/clearml/start', {
    method: 'POST',
    body: JSON.stringify(payload ?? {}),
  });
}

/**
 * POST /api/v1/stack/clearml/stop
 */
export async function stopClearMLStack(): Promise<{ status?: string; message?: string } & Record<string, unknown>> {
  return request<{ status?: string; message?: string } & Record<string, unknown>>('/api/v1/stack/clearml/stop', {
    method: 'POST',
  });
}

/**
 * GET /api/v1/stack/clearml/status
 */
export async function getClearMLStackStatus(): Promise<ClearMLStackStatus> {
  return request<ClearMLStackStatus>('/api/v1/stack/clearml/status', { method: 'GET' });
}

/**
 * Utility to detect server-side gating (403 Disabled)
 */
export function isStackControlForbidden(error: unknown): boolean {
  return error instanceof StackAPIError && error.status === 403;
}

/**
 * Utility to format status safely for UI
 */
export function extractStackLinks(status: ClearMLStackStatus | null | undefined): {
  web?: string;
  api?: string;
  file?: string;
} {
  if (!status) return {};
  const { web_url, api_url, file_url } = status;
  return { web: web_url, api: api_url, file: file_url };
}
