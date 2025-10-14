export interface UserSafe {
  id: string;
  email: string;
  is_active: boolean;
  subscription_status: string;
  created_at: string;
  updated_at: string;
}

export interface AuthLoginResponse {
  access_token: string;
  token_type: 'bearer';
}

export interface AuthRegisterRequest {
  email: string;
  password: string;
}

export interface AuthLoginRequest {
  email: string;
  password: string;
}

export class ClientError extends Error {
  status: number;
  code?: string;
  details?: Record<string, unknown>;

  constructor(status: number, message: string, code?: string, details?: Record<string, unknown>) {
    super(message);
    this.name = 'ClientError';
    this.status = status;
    this.code = code;
    this.details = details;
  }
}