import { toast } from 'react-hot-toast';

// Base API URL (Vite env; fallback to relative for proxy)
const API_BASE = import.meta.env.VITE_API_URL || '/api/v1';

// Error handler (shared)
const handleApiError = (error: unknown, action: string) => {
  console.error(`Medusa API ${action} failed:`, error);
  if (typeof toast !== 'undefined') {
    toast.error(`Failed to ${action}: ${error instanceof Error ? error.message : 'Unknown error'}`);
  }
};

// GET /api/v1/medusa/status
export async function getMedusaStatus() {
  try {
    const response = await fetch(`${API_BASE}/medusa/status`);
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    return await response.json() as { status: 'running' | 'stopped'; pid: number | null };
  } catch (error) {
    handleApiError(error, 'fetch status');
    throw error;
  }
}

// POST /api/v1/medusa/start
export async function startMedusaTrainer() {
  try {
    const response = await fetch(`${API_BASE}/medusa/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    });
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    return await response.json() as { status: string; message: string };
  } catch (error) {
    handleApiError(error, 'start trainer');
    throw error;
  }
}

// POST /api/v1/medusa/stop
export async function stopMedusaTrainer() {
  try {
    const response = await fetch(`${API_BASE}/medusa/stop`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    });
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    return await response.json() as { status: string; message: string };
  } catch (error) {
    handleApiError(error, 'stop trainer');
    throw error;
  }
}

// GET /api/v1/medusa/logs (returns plain text)
export async function getMedusaLogs() {
  try {
    const response = await fetch(`${API_BASE}/medusa/logs`);
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    return await response.text();
  } catch (error) {
    handleApiError(error, 'fetch logs');
    throw error;
  }
}

// GET /api/v1/medusa/analysis
export async function getMedusaAnalysis() {
  try {
    const response = await fetch(`${API_BASE}/medusa/analysis`);
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    return await response.json();
  } catch (error) {
    handleApiError(error, 'fetch analysis');
    throw error;
  }
}