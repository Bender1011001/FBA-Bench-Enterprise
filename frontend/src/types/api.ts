/**
 * Types for Phase 1 backend endpoints used by Control Center
 */

export interface HttpError { status?: number; body?: any; message: string; }

export interface ClearMLStackPorts {
  web?: boolean;
  api?: boolean;
  file?: boolean;
  [key: string]: boolean | undefined;
}

export interface ClearMLStackStatus {
  status?: string;
  message?: string;
  web_url?: string;
  api_url?: string;
  file_url?: string;
  ports?: ClearMLStackPorts;
  enabled?: boolean;
  disabled?: boolean;
  [key: string]: any;
}

export interface ClearMLStackStartRequest { compose_path?: string; }

export type ClearMLStackStartResponse = ClearMLStackStatus;

export type ClearMLStackStopResponse = { status?: string; message?: string } & Record<string, any>;

export interface SimulationActionResponse {
  status?: string;
  message?: string;
  [key: string]: any;
}

export interface SimulationSnapshot {
  status?: string;
  day?: number;
  tick?: number;
  [key: string]: any;
}

export interface SimulationSpeedRequest { speed: number; }

export type SettingsPayload = Record<string, any>;
export type SettingsResponse = Record<string, any>;

export type RuntimeConfig = Record<string, any>;
