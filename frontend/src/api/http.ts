import type { TokenStorage } from './tokenStorage';

export interface UserPublic {
  id: string;
  email: string;
  is_active: boolean;
  subscription_status: string;
  created_at: string;
  updated_at: string;
}

export interface ApiError {
  status: number;
  message: string;
  details?: string;
}

export interface ValidationError extends ApiError {
  status: 400;
  message: 'ValidationError';
}

export interface AuthError extends ApiError {
  status: 401;
  message: 'AuthError';
  reason: 'invalid_credentials' | 'unauthorized';
}

export interface ConflictError extends ApiError {
  status: 409;
  message: 'ConflictError';
  details: 'email_already_registered';
}

type TypedError = ApiError | ValidationError | AuthError | ConflictError;

interface HttpClient {
  get<T>(path: string): Promise<T>;
  post<T>(path: string, body?: unknown): Promise<T>;
}

export function createHttpClient({ baseUrl = 'http://localhost:8000', storage }: { baseUrl?: string; storage: TokenStorage }): HttpClient {
  const getHeaders = (extraHeaders: Record<string, string> = {}): HeadersInit => {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...extraHeaders,
    };

    const authHeader = storage.getAuthHeader();
    if (Object.keys(authHeader).length > 0) {
      Object.assign(headers, authHeader);
    }

    return headers;
  };

  const handleResponse = async <T>(response: Response): Promise<T> => {
    const contentType = response.headers.get('content-type');
    if (!contentType?.includes('application/json')) {
      throw new Error(`Unexpected content type: ${contentType}`);
    }

    const body = await response.json() as { detail?: string };

    if (response.ok) {
      return body as T;
    }

    const status = response.status;
    const detail = body.detail ?? 'unknown_error';
    const message = detail;

    let error: TypedError;
    switch (status) {
      case 400:
        error = { status, message: 'ValidationError', details: message } as ValidationError;
        break;
      case 401:
        const reason = message.includes('credentials') ? 'invalid_credentials' : 'unauthorized';
        error = { status, message: 'AuthError', reason, details: message } as AuthError;
        break;
      case 409:
        error = { status, message: 'ConflictError', details: 'email_already_registered' } as ConflictError;
        break;
      default:
        error = { status, message, details: message } as ApiError;
    }

    throw error;
  };

  const request = async <T>(url: string, options: RequestInit = {}): Promise<T> => {
    const response = await fetch(url, {
      ...options,
      headers: getHeaders(options.headers as Record<string, string> || {}),
    });

    return handleResponse<T>(response);
  };

  return {
    async get<T>(path: string): Promise<T> {
      const url = new URL(path, baseUrl);
      return request<T>(url.toString(), { method: 'GET' });
    },

    async post<T>(path: string, body?: unknown): Promise<T> {
      const url = new URL(path, baseUrl);
      const init: RequestInit = { method: 'POST' };
      if (body !== undefined) {
        init.body = JSON.stringify(body);
      }
      return request<T>(url.toString(), init);
    },
  };
}