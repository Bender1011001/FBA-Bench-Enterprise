import type { TokenStorage } from './tokenStorage';
import { createTokenStorage } from './tokenStorage';
import { createHttpClient, type UserPublic, type ApiError } from './http';

export interface TokenResponse {
  access_token: string;
  token_type: 'bearer';
  expires_in: number;
}

export function createAuthClient(opts?: { baseUrl?: string; storage?: TokenStorage }) {
  const baseUrl = opts?.baseUrl || (typeof import.meta !== 'undefined' ? import.meta.env.VITE_API_BASE_URL as string : process.env.VITE_API_BASE_URL) || 'http://localhost:8000';
  const storage = opts?.storage || createTokenStorage();
  const http = createHttpClient({ baseUrl, storage });

  const normalizeEmail = (email: string): string => email.trim().toLowerCase();

  const validateCredentials = (email: string, password: string): void => {
    if (!email || email.trim().length === 0) {
      throw new Error('Email is required');
    }
    if (password.length < 8 || password.length > 128) {
      throw new Error('Password must be between 8 and 128 characters');
    }
  };

  return {
    async register(email: string, password: string): Promise<UserPublic> {
      validateCredentials(email, password);
      const normalizedEmail = normalizeEmail(email);
      const response = await http.post<UserPublic>('/auth/register', { email: normalizedEmail, password });
      return response;
    },

    async login(email: string, password: string): Promise<TokenResponse> {
      validateCredentials(email, password);
      const normalizedEmail = normalizeEmail(email);
      const response = await http.post<TokenResponse>('/auth/login', { email: normalizedEmail, password });
      if (response.token_type !== 'bearer') {
        throw new Error('Invalid token type');
      }
      storage.setToken(response.access_token);
      return response;
    },

    async me(): Promise<UserPublic> {
      try {
        return await http.get<UserPublic>('/auth/me');
      } catch (error) {
        if ((error as ApiError).status === 401) {
          storage.clearToken();
          throw error;
        }
        throw error;
      }
    },
  };
}