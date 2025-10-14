import { request } from './http';
import { setToken } from '../auth/tokenStorage';
import type { UserSafe, AuthLoginResponse, AuthRegisterRequest, AuthLoginRequest } from '../types/auth';

export async function register(payload: AuthRegisterRequest): Promise<UserSafe> {
  return request<UserSafe>('/auth/register', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function login(payload: AuthLoginRequest): Promise<AuthLoginResponse> {
  const response = await request<AuthLoginResponse>('/auth/login', {
    method: 'POST',
    body: JSON.stringify(payload),
  });

  if (response.access_token) {
    setToken(response.access_token);
  }

  return response;
}

export async function me(): Promise<UserSafe> {
  return request<UserSafe>('/me');
}