export interface TokenStorage {
  getToken(): string | null;
  setToken(token: string): void;
  clearToken(): void;
  isAuthenticated(): boolean;
  getAuthHeader(): Record<string, string> | {};
}

class LocalStorageTokenStorage implements TokenStorage {
  private readonly key = 'fbaee_access_token';
  private cache: string | null = null;

  constructor() {
    if (typeof window === 'undefined') {
      throw new Error('LocalStorageTokenStorage is not available in non-browser environments');
    }
    // Load cache on init
    this.cache = localStorage.getItem(this.key);
  }

  getToken(): string | null {
    // Return cache if available, else load from storage
    if (this.cache !== null) {
      return this.cache;
    }
    this.cache = localStorage.getItem(this.key);
    return this.cache;
  }

  setToken(token: string): void {
    this.cache = token;
    localStorage.setItem(this.key, token);
  }

  clearToken(): void {
    this.cache = null;
    localStorage.removeItem(this.key);
  }

  isAuthenticated(): boolean {
    return this.getToken() !== null;
  }

  getAuthHeader(): Record<string, string> {
    const token = this.getToken();
    if (!token) {
      return {};
    }
    return { Authorization: `Bearer ${token}` };
  }
}

class InMemoryTokenStorage implements TokenStorage {
  private token: string | null = null;

  getToken(): string | null {
    return this.token;
  }

  setToken(token: string): void {
    this.token = token;
  }

  clearToken(): void {
    this.token = null;
  }

  isAuthenticated(): boolean {
    return this.getToken() !== null;
  }

  getAuthHeader(): Record<string, string> {
    const token = this.getToken();
    if (!token) {
      return {};
    }
    return { Authorization: `Bearer ${token}` };
  }
}

export const createTokenStorage = (useLocalStorage: boolean = typeof window !== 'undefined'): TokenStorage => {
  if (useLocalStorage) {
    return new LocalStorageTokenStorage();
  }
  return new InMemoryTokenStorage();
};

export { LocalStorageTokenStorage, InMemoryTokenStorage };