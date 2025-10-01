/**
 * Environment Service for FBA-Bench Dashboard
 * 
 * Manages API keys and credentials in localStorage with validation and security patterns.
 * Provides a clean interface for storing/retrieving environment variables that would
 * typically be in .env files, adapted for browser environment.
 * 
 * Security Features:
 * - Secure localStorage operations with encryption-like obfuscation
 * - Key validation helpers for each service
 * - Clear warnings about localStorage limitations
 * - No console logging of sensitive data
 * 
 * Supported Services:
 * - OpenAI API
 * - OpenRouter API  
 * - ClearML (access key + secret key)
 */

export interface EnvironmentConfig {
  openaiApiKey?: string;
  openrouterApiKey?: string;
  clearmlAccessKey?: string;
  clearmlSecretKey?: string;
}

export interface ServiceStatus {
  service: string;
  configured: boolean;
  lastTested?: Date;
  testResult?: 'success' | 'failed' | 'pending';
}

export interface ConnectionTestResult {
  success: boolean;
  message: string;
  details?: string;
}

// Storage keys with prefixes for organization
const STORAGE_KEYS = {
  OPENAI_API_KEY: 'fba_env_openai_key',
  OPENROUTER_API_KEY: 'fba_env_openrouter_key', 
  CLEARML_ACCESS_KEY: 'fba_env_clearml_access',
  CLEARML_SECRET_KEY: 'fba_env_clearml_secret',
  CONFIG_STATUS: 'fba_env_status',
} as const;

class EnvironmentService {
  private readonly storagePrefix = 'fba_env_';

  /**
   * Simple obfuscation for localStorage values (not true encryption, but better than plaintext)
   */
  private encode(value: string): string {
    return btoa(value);
  }

  private decode(value: string): string {
    try {
      return atob(value);
    } catch {
      return value; // Fallback if not encoded
    }
  }

  /**
   * Store API key securely in localStorage
   */
  setApiKey(service: keyof typeof STORAGE_KEYS, key: string): void {
    if (!key.trim()) {
      this.clearApiKey(service);
      return;
    }

    try {
      const encodedKey = this.encode(key.trim());
      localStorage.setItem(STORAGE_KEYS[service], encodedKey);
      
      // Update status
      this.updateServiceStatus(service.toLowerCase().replace('_', ''), {
        configured: true,
        testResult: undefined, // Reset test result when key changes
      });
    } catch (error) {
      console.error(`Failed to store ${service}:`, error);
      throw new Error(`Failed to store API key for ${service}`);
    }
  }

  /**
   * Retrieve API key from localStorage
   */
  getApiKey(service: keyof typeof STORAGE_KEYS): string | null {
    try {
      const encodedKey = localStorage.getItem(STORAGE_KEYS[service]);
      if (!encodedKey) return null;
      
      return this.decode(encodedKey);
    } catch (error) {
      console.error(`Failed to retrieve ${service}:`, error);
      return null;
    }
  }

  /**
   * Remove API key from localStorage
   */
  clearApiKey(service: keyof typeof STORAGE_KEYS): void {
    try {
      localStorage.removeItem(STORAGE_KEYS[service]);
      
      // Update status
      this.updateServiceStatus(service.toLowerCase().replace('_', ''), {
        configured: false,
        testResult: undefined,
      });
    } catch (error) {
      console.error(`Failed to clear ${service}:`, error);
    }
  }

  /**
   * Get all stored API keys (useful for checking status)
   */
  getStoredApiKeys(): EnvironmentConfig {
    return {
      openaiApiKey: this.getApiKey('OPENAI_API_KEY') || undefined,
      openrouterApiKey: this.getApiKey('OPENROUTER_API_KEY') || undefined,
      clearmlAccessKey: this.getApiKey('CLEARML_ACCESS_KEY') || undefined,
      clearmlSecretKey: this.getApiKey('CLEARML_SECRET_KEY') || undefined,
    };
  }

  /**
   * Clear all stored API keys
   */
  clearApiKeys(): void {
    Object.keys(STORAGE_KEYS).forEach(key => {
      this.clearApiKey(key as keyof typeof STORAGE_KEYS);
    });
    localStorage.removeItem(STORAGE_KEYS.CONFIG_STATUS);
  }

  /**
   * Check which services are configured
   */
  getServiceStatuses(): ServiceStatus[] {
    const config = this.getStoredApiKeys();
    const storedStatus = this.getStoredStatus();

    return [
      {
        service: 'OpenAI',
        configured: !!config.openaiApiKey,
        ...storedStatus.openai,
      },
      {
        service: 'OpenRouter', 
        configured: !!config.openrouterApiKey,
        ...storedStatus.openrouter,
      },
      {
        service: 'ClearML',
        configured: !!(config.clearmlAccessKey && config.clearmlSecretKey),
        ...storedStatus.clearml,
      },
    ];
  }

  /**
   * Validate API key format for each service
   */
  validateApiKey(service: string, key: string): { valid: boolean; message: string } {
    if (!key.trim()) {
      return { valid: false, message: 'API key cannot be empty' };
    }

    switch (service.toLowerCase()) {
      case 'openai':
        if (!key.startsWith('sk-')) {
          return { valid: false, message: 'OpenAI API keys must start with "sk-"' };
        }
        if (key.length < 50) {
          return { valid: false, message: 'OpenAI API key appears to be too short' };
        }
        break;
        
      case 'openrouter':
        if (!key.startsWith('sk-or-')) {
          return { valid: false, message: 'OpenRouter API keys must start with "sk-or-"' };
        }
        break;
        
      case 'clearml':
        // ClearML keys can vary in format, so just check basic requirements
        if (key.length < 8) {
          return { valid: false, message: 'ClearML key appears to be too short' };
        }
        break;
        
      default:
        return { valid: false, message: 'Unknown service' };
    }

    return { valid: true, message: 'API key format is valid' };
  }

  /**
   * Store service test results and status
   */
  private updateServiceStatus(service: string, status: Partial<Omit<ServiceStatus, 'service'>>): void {
    try {
      const stored = this.getStoredStatus();
      const updated = {
        ...stored,
        [service]: {
          ...stored[service],
          ...status,
          lastTested: status.testResult ? new Date() : stored[service]?.lastTested,
        },
      };
      
      localStorage.setItem(STORAGE_KEYS.CONFIG_STATUS, JSON.stringify(updated));
    } catch (error) {
      console.error('Failed to update service status:', error);
    }
  }

  /**
   * Get stored service statuses
   */
  private getStoredStatus(): Record<string, Partial<ServiceStatus>> {
    try {
      const stored = localStorage.getItem(STORAGE_KEYS.CONFIG_STATUS);
      if (!stored) return {};
      
      const parsed = JSON.parse(stored);
      
      // Convert date strings back to Date objects
      Object.keys(parsed).forEach((key) => {
        const status = parsed[key];
        if (status && typeof status === 'object' && 'lastTested' in status && typeof status.lastTested === 'string') {
          (status as { lastTested: string | Date }).lastTested = new Date(status.lastTested);
        }
      });
      
      return parsed;
    } catch {
      return {};
    }
  }

  /**
   * Update test result for a service
   */
  setTestResult(service: string, result: 'success' | 'failed'): void {
    this.updateServiceStatus(service.toLowerCase(), {
      testResult: result,
    });
  }

  /**
   * Check if any critical keys are missing
   */
  getMissingCriticalKeys(): string[] {
    const config = this.getStoredApiKeys();
    const missing: string[] = [];

    // All keys are optional according to CLI, but we can highlight what's missing
    if (!config.openaiApiKey) missing.push('OpenAI API Key');
    if (!config.openrouterApiKey) missing.push('OpenRouter API Key');
    if (!config.clearmlAccessKey || !config.clearmlSecretKey) {
      missing.push('ClearML Credentials');
    }

    return missing;
  }

  /**
   * Check if basic setup is complete (at least one LLM provider + ClearML)
   */
  isBasicSetupComplete(): boolean {
    const config = this.getStoredApiKeys();
    const hasLLMProvider = !!(config.openaiApiKey || config.openrouterApiKey);
    const hasClearML = !!(config.clearmlAccessKey && config.clearmlSecretKey);
    
    return hasLLMProvider && hasClearML;
  }

  /**
   * Get help text for obtaining API keys
   */
  getKeyObtainInstructions(service: string): { title: string; instructions: string; url?: string } {
    switch (service.toLowerCase()) {
      case 'openai':
        return {
          title: 'Getting an OpenAI API Key',
          instructions: 'Sign up at OpenAI, go to API keys section, and create a new secret key. Keys start with "sk-".',
          url: 'https://platform.openai.com/api-keys',
        };
        
      case 'openrouter':
        return {
          title: 'Getting an OpenRouter API Key',
          instructions: 'Sign up at OpenRouter, go to Keys section, and create a new API key. Keys start with "sk-or-".',
          url: 'https://openrouter.ai/keys',
        };
        
      case 'clearml':
        return {
          title: 'Getting ClearML Credentials',
          instructions: 'For local development, you can use the default credentials (admin@clearml.com / clearml123). For production, create an account and get your access/secret keys from the profile settings.',
          url: 'http://localhost:8080/profile',
        };
        
      default:
        return {
          title: 'Unknown Service',
          instructions: 'Please refer to the service documentation for API key instructions.',
        };
    }
  }

  /**
   * Export configuration (without revealing actual keys)
   */
  exportConfigStatus(): {
    configuredServices: string[];
    missingServices: string[];
    basicSetupComplete: boolean;
    lastUpdated: Date;
  } {
    const statuses = this.getServiceStatuses();
    
    return {
      configuredServices: statuses.filter(s => s.configured).map(s => s.service),
      missingServices: statuses.filter(s => !s.configured).map(s => s.service),
      basicSetupComplete: this.isBasicSetupComplete(),
      lastUpdated: new Date(),
    };
  }
}

// Export singleton instance
export const environmentService = new EnvironmentService();
