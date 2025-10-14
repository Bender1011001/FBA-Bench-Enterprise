// Token storage module with localStorage primary and in-memory fallback
const STORAGE_KEY = 'fba.auth.access_token';
let inMemoryToken: string | null = null;

function isLocalStorageAvailable(): boolean {
  try {
    const test = '__storage_test__';
    localStorage.setItem(test, test);
    localStorage.removeItem(test);
    return true;
  } catch (e) {
    return false;
  }
}

export function setToken(token: string): void {
  if (isLocalStorageAvailable()) {
    localStorage.setItem(STORAGE_KEY, token);
  } else {
    inMemoryToken = token;
  }
}

export function getToken(): string | null {
  if (isLocalStorageAvailable()) {
    return localStorage.getItem(STORAGE_KEY);
  }
  return inMemoryToken;
}

export function clearToken(): void {
  if (isLocalStorageAvailable()) {
    localStorage.removeItem(STORAGE_KEY);
  }
  inMemoryToken = null;
}