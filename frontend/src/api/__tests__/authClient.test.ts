import { describe, it, expect, vi, beforeEach } from 'vitest';
import { createAuthClient } from '../authClient';
import { createTokenStorage } from '../tokenStorage';
import type { TokenStorage } from '../tokenStorage';
import type { UserPublic, ApiError } from '../http';
import type { TokenResponse } from '../authClient';

// Mock fetch globally
global.fetch = vi.fn() as any;

describe('authClient', () => {
  let mockStorage: TokenStorage;
  let mockClient: ReturnType<typeof createAuthClient>;

  beforeEach(() => {
    vi.clearAllMocks();
    (global.fetch as any).mockReset();
    mockStorage = {
      getToken: vi.fn(),
      setToken: vi.fn(),
      clearToken: vi.fn(),
      isAuthenticated: vi.fn(),
      getAuthHeader: vi.fn(() => ({})),
    };
    mockClient = createAuthClient({ storage: mockStorage });
  });

  describe('register', () => {
    it('returns UserPublic on 201 success', async () => {
      const mockUser: UserPublic = {
        id: '123',
        email: 'user@example.com',
        is_active: true,
        subscription_status: 'active',
        created_at: '2023-01-01T00:00:00Z',
        updated_at: '2023-01-01T00:00:00Z',
      };
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        status: 201,
        headers: { get: () => 'application/json' },
        json: vi.fn().mockResolvedValueOnce(mockUser),
      });

      const result = await mockClient.register('user@example.com', 'password123');

      expect(result).toEqual(mockUser);
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/auth/register'),
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({ 'Content-Type': 'application/json' }),
          body: JSON.stringify({ email: 'user@example.com', password: 'password123' }),
        })
      );
    });

    it('normalizes email (trim + lowercase)', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        status: 201,
        headers: { get: () => 'application/json' },
        json: vi.fn().mockResolvedValueOnce({}),
      });

      await mockClient.register(' User@Example.COM ', 'password123');

      expect(global.fetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          body: JSON.stringify({ email: 'user@example.com', password: 'password123' }),
        })
      );
    });

    it('maps 409 to ConflictError', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 409,
        headers: { get: () => 'application/json' },
        json: vi.fn().mockResolvedValueOnce({ detail: 'email already registered' }),
      });

      await expect(mockClient.register('user@example.com', 'password123')).rejects.toMatchObject({
        status: 409,
        message: 'ConflictError',
        details: 'email_already_registered',
      });
    });

    it('maps 400 to ValidationError', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 400,
        headers: { get: () => 'application/json' },
        json: vi.fn().mockResolvedValueOnce({ detail: 'Invalid password' }),
      });

      await expect(mockClient.register('user@example.com', 'short')).rejects.toMatchObject({
        status: 400,
        message: 'ValidationError',
        details: 'Invalid password',
      });
    });

    it('throws on invalid credentials', async () => {
      await expect(mockClient.register('', 'password123')).rejects.toThrow('Email is required');
      await expect(mockClient.register('user@example.com', 'short')).rejects.toThrow('Password must be between 8 and 128 characters');
    });
  });

  describe('login', () => {
    it('stores token and returns TokenResponse on success', async () => {
      const mockTokens: TokenResponse = {
        access_token: 'mock_token',
        token_type: 'bearer',
        expires_in: 900,
      };
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        status: 200,
        headers: { get: () => 'application/json' },
        json: vi.fn().mockResolvedValueOnce(mockTokens),
      });

      const result = await mockClient.login('user@example.com', 'password123');

      expect(result).toEqual(mockTokens);
      expect(mockStorage.setToken).toHaveBeenCalledWith('mock_token');
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/auth/login'),
        expect.objectContaining({
          body: JSON.stringify({ email: 'user@example.com', password: 'password123' }),
        })
      );
    });

    it('normalizes email for login', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        status: 200,
        headers: { get: () => 'application/json' },
        json: vi.fn().mockResolvedValueOnce({}),
      });

      await mockClient.login(' User@Example.COM ', 'password123');

      expect(global.fetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          body: JSON.stringify({ email: 'user@example.com', password: 'password123' }),
        })
      );
    });

    it('maps 401 to AuthError', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 401,
        headers: { get: () => 'application/json' },
        json: vi.fn().mockResolvedValueOnce({ detail: 'Invalid credentials' }),
      });

      await expect(mockClient.login('user@example.com', 'wrong')).rejects.toMatchObject({
        status: 401,
        message: 'AuthError',
        reason: 'invalid_credentials',
      });
      expect(mockStorage.setToken).not.toHaveBeenCalled();
    });

    it('throws on invalid token_type', async () => {
      const invalidResponse = { access_token: 'token', token_type: 'invalid' as any, expires_in: 900 };
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        status: 200,
        headers: { get: () => 'application/json' },
        json: vi.fn().mockResolvedValueOnce(invalidResponse),
      });

      await expect(mockClient.login('user@example.com', 'password123')).rejects.toThrow('Invalid token type');
      expect(mockStorage.setToken).not.toHaveBeenCalled();
    });

    it('throws on invalid credentials', async () => {
      await expect(mockClient.login('', 'password123')).rejects.toThrow('Email is required');
    });
  });

  describe('me', () => {
    it('returns UserPublic on 200 with auth header when token present', async () => {
      vi.mocked(mockStorage.getAuthHeader).mockReturnValueOnce({ Authorization: 'Bearer mock_token' });
      const mockUser: UserPublic = { id: '123', email: 'user@example.com', is_active: true, subscription_status: 'active', created_at: '2023-01-01T00:00:00Z', updated_at: '2023-01-01T00:00:00Z' };
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        status: 200,
        headers: { get: () => 'application/json' },
        json: vi.fn().mockResolvedValueOnce(mockUser),
      });

      const result = await mockClient.me();

      expect(result).toEqual(mockUser);
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/auth/me'),
        expect.objectContaining({
          method: 'GET',
          headers: expect.objectContaining({ Authorization: 'Bearer mock_token' }),
        })
      );
    });

    it('maps 401 to AuthError and clears token', async () => {
      vi.mocked(mockStorage.getAuthHeader).mockReturnValueOnce({ Authorization: 'Bearer mock_token' });
      (global.fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 401,
        headers: { get: () => 'application/json' },
        json: vi.fn().mockResolvedValueOnce({ detail: 'Unauthorized' }),
      });

      await expect(mockClient.me()).rejects.toMatchObject({
        status: 401,
        message: 'AuthError',
        reason: 'unauthorized',
      });
      expect(mockStorage.clearToken).toHaveBeenCalled();
    });

    it('does not leak token in error messages', async () => {
      vi.mocked(mockStorage.getAuthHeader).mockReturnValueOnce({ Authorization: 'Bearer secret_token' });
      (global.fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 401,
        headers: { get: () => 'application/json' },
        json: vi.fn().mockResolvedValueOnce({ detail: 'Token invalid' }),
      });

      const error = await mockClient.me().catch((e) => e);
      expect((error as ApiError).details).toBe('Token invalid');
      expect((error as ApiError).details).not.toContain('secret_token');
    });

    it('calls without auth header if no token', async () => {
      vi.mocked(mockStorage.getAuthHeader).mockReturnValueOnce({});
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        status: 200,
        headers: { get: () => 'application/json' },
        json: vi.fn().mockResolvedValueOnce({}),
      });

      await mockClient.me();

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/auth/me'),
        expect.objectContaining({
          method: 'GET',
          headers: expect.objectContaining({ 'Content-Type': 'application/json' }),
        })
      );
      expect(global.fetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.not.objectContaining({
          headers: expect.objectContaining({ Authorization: expect.any(String) }),
        })
      );
    });
  });
});