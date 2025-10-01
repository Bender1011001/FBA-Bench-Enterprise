/**
 * Global Application Store
 * 
 * Zustand-based state management for the FBA-Bench dashboard.
 * Manages application state, experiments, real-time data, and UI state.
 */

import { create } from 'zustand';
import { subscribeWithSelector } from 'zustand/middleware';
import { Experiment, SystemStats, LeaderboardEntry } from '../services/api';

// Types
interface ConnectionStatus {
  apiConnected: boolean;
  clearmlConnected: boolean;
  wsConnected: boolean;
}

interface Notification {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  message: string;
  timestamp: Date;
  read: boolean;
}

interface AppState {
  // Connection status
  connectionStatus: ConnectionStatus;
  
  // Data
  experiments: Experiment[];
  systemStats: SystemStats | null;
  leaderboard: LeaderboardEntry[];
  
  // UI State
  selectedExperiment: string | null;
  sidebarCollapsed: boolean;
  theme: 'light' | 'dark';
  
  // Loading states
  loading: {
    experiments: boolean;
    stats: boolean;
    leaderboard: boolean;
  };
  
  // Notifications
  notifications: Notification[];
  
  // Filters and search
  filters: {
    status: string[];
    project: string;
    searchQuery: string;
  };
}

interface AppActions {
  // Connection
  setConnectionStatus: (status: Partial<ConnectionStatus>) => void;
  
  // Data actions
  setExperiments: (experiments: Experiment[]) => void;
  updateExperiment: (experiment: Experiment) => void;
  setSystemStats: (stats: SystemStats) => void;
  setLeaderboard: (leaderboard: LeaderboardEntry[]) => void;
  
  // UI actions
  setSelectedExperiment: (id: string | null) => void;
  toggleSidebar: () => void;
  setTheme: (theme: 'light' | 'dark') => void;
  
  // Loading actions
  setLoading: (key: keyof AppState['loading'], value: boolean) => void;
  
  // Notifications
  addNotification: (notification: Omit<Notification, 'id' | 'timestamp' | 'read'>) => void;
  markNotificationRead: (id: string) => void;
  clearNotifications: () => void;
  
  // Filters
  setFilters: (filters: Partial<AppState['filters']>) => void;
  clearFilters: () => void;
}

type AppStore = AppState & AppActions;

export const useAppStore = create<AppStore>()(
  subscribeWithSelector((set) => ({
    // Initial state
    connectionStatus: {
      apiConnected: false,
      clearmlConnected: false,
      wsConnected: false,
    },
    
    experiments: [],
    systemStats: null,
    leaderboard: [],
    
    selectedExperiment: null,
    sidebarCollapsed: false,
    theme: 'dark',
    
    loading: {
      experiments: false,
      stats: false,
      leaderboard: false,
    },
    
    notifications: [],
    
    filters: {
      status: [],
      project: 'FBA-Bench',
      searchQuery: '',
    },

    // Actions
    setConnectionStatus: (status) =>
      set((state) => ({
        connectionStatus: { ...state.connectionStatus, ...status },
      })),

    setExperiments: (experiments) =>
      set(() => {
        // Normalize to a flat Experiment[]. Accepts arrays (including nested), strings (JSON),
        // envelopes { items: [] } | { experiments: [] }, and keyed maps.
        const toArray = (input: unknown): Experiment[] => {
          if (Array.isArray(input)) {
            return (input as unknown[]).flatMap((v) =>
              Array.isArray(v) ? (v as Experiment[]) : [v as Experiment]
            );
          }
          if (typeof input === 'string') {
            try {
              return toArray(JSON.parse(input));
            } catch {
              return [];
            }
          }
          if (input && typeof input === 'object') {
            const obj = input as Record<string, unknown>;
            const items = (obj as { items?: unknown }).items;
            if (Array.isArray(items)) return items as Experiment[];
            const experimentsKey = (obj as { experiments?: unknown }).experiments;
            if (Array.isArray(experimentsKey)) return experimentsKey as Experiment[];
            return Object.values(obj) as Experiment[];
          }
          return [];
        };

        const normalized: Experiment[] = toArray(experiments as unknown);
        return { experiments: normalized };
      }),

    updateExperiment: (experiment) =>
      set((state) => ({
        experiments: state.experiments.map((exp) =>
          exp.id === experiment.id ? experiment : exp
        ),
      })),

    setSystemStats: (systemStats) => set({ systemStats }),

    setLeaderboard: (leaderboard) => set({ leaderboard }),

    setSelectedExperiment: (selectedExperiment) => set({ selectedExperiment }),

    toggleSidebar: () =>
      set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),

    setTheme: (theme) => set({ theme }),

    setLoading: (key, value) =>
      set((state) => ({
        loading: { ...state.loading, [key]: value },
      })),

    addNotification: (notification) =>
      set((state) => ({
        notifications: [
          {
            ...notification,
            id: Date.now().toString(),
            timestamp: new Date(),
            read: false,
          },
          ...state.notifications,
        ].slice(0, 50), // Keep only last 50 notifications
      })),

    markNotificationRead: (id) =>
      set((state) => ({
        notifications: state.notifications.map((notif) =>
          notif.id === id ? { ...notif, read: true } : notif
        ),
      })),

    clearNotifications: () => set({ notifications: [] }),

    setFilters: (filters) =>
      set((state) => ({
        filters: { ...state.filters, ...filters },
      })),

    clearFilters: () =>
      set({
        filters: {
          status: [],
          project: 'FBA-Bench',
          searchQuery: '',
        },
      }),
  }))
);

// Selectors for better performance
export const useConnectionStatus = () => useAppStore((state) => state.connectionStatus);
export const useExperiments = () => useAppStore((state) => state.experiments);
export const useSystemStats = () => useAppStore((state) => state.systemStats);
export const useLeaderboard = () => useAppStore((state) => state.leaderboard);
export const useSelectedExperiment = () => useAppStore((state) => state.selectedExperiment);
export const useNotifications = () => useAppStore((state) => state.notifications);
export const useFilters = () => useAppStore((state) => state.filters);
export const useLoading = () => useAppStore((state) => state.loading);