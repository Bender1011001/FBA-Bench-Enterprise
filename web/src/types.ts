export interface UserPublic {
  id: string;
  email: string;
  created_at: string;
  updated_at: string;
  is_active: boolean;
  subscription_status: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: 'bearer';
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface AuthError {
  name: string;
  status?: number;
  detail?: string;
}