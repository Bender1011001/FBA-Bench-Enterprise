/**
 * ClearML Service for FBA-Bench Game Dashboard
 * 
 * Fetches data from ClearML REST API to power game-like UI elements:
 * - Quests: Experiments/tasks as missions with levels (tiers) and rewards (metrics).
 * - Stats: Real-time scalars as player attributes (e.g., Profit as Health, Market Share as Power).
 * - Leaderboard: Top tasks by composite score, with avatars (model icons).
 * 
 * API Base: Defaults to local ClearML API (http://localhost:8008).
 * Auth: Uses access_key/secret_key from env or prompt; for local, often not needed.
 * 
 * Usage:
 * - Initialize: new ClearMLService({ apiHost: 'http://localhost:8008' });
 * - Fetch quests: service.getQuests(project='FBA-Bench');
 * - Poll stats: service.getLiveStats(taskId);
 * 
 * Game Integration:
 * - Maps ClearML scalars to game stats with icons/colors.
 * - Adds animations-ready data (e.g., progress bars for objectives).
 * - Fallback to mock data if API unavailable for dev.
 */

interface ClearMLConfig {
  apiHost: string;
  accessKey?: string;
  secretKey?: string;
  project?: string;
}

interface Quest {
  id: string;
  name: string;
  status: 'active' | 'completed' | 'failed' | 'queued';
  level: number; // Difficulty tier as game level
  score: number; // Composite score
  rewards: string[]; // Met objectives as rewards
  progress: number; // 0-100% completion
  icon: string; // Lucide icon name
}

interface Stat {
  name: string;
  value: number;
  max: number;
  unit: string;
  icon: string; // Lucide icon
  color: string; // Tailwind class (e.g., 'text-blue-500')
  animation: 'pulse' | 'bounce' | 'none'; // For framer-motion
}

interface LeaderboardEntry {
  rank: number;
  player: string; // Model/agent name
  score: number;
  avatar: string; // Emoji or icon
  badge: string; // 'gold' | 'silver' | 'bronze'
}

export class ClearMLService {
  private apiHost: string;
  private accessKey: string | null;
  private secretKey: string | null;
  private project: string;
  private token: string | null = null; // For auth header

  constructor(config: ClearMLConfig) {
    this.apiHost = config.apiHost || 'http://localhost:8008';
    this.accessKey = config.accessKey || null;
    this.secretKey = config.secretKey || null;
    this.project = config.project || 'FBA-Bench';
    this.initializeAuth();
  }

  private async initializeAuth() {
    if (this.accessKey && this.secretKey) {
      // Generate token for API calls (ClearML uses basic auth or token)
      const response = await fetch(`${this.apiHost}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ access_key: this.accessKey, secret_key: this.secretKey }),
      });
      if (response.ok) {
        const data = await response.json();
        this.token = data.token;
      }
    }
  }

  private getAuthHeaders() {
    const headers = { 'Content-Type': 'application/json' };
    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    } else if (this.accessKey && this.secretKey) {
      // Fallback to basic auth
      const creds = btoa(`${this.accessKey}:${this.secretKey}`);
      headers['Authorization'] = `Basic ${creds}`;
    }
    return headers;
  }

  async getQuests(): Promise<Quest[]> {
    try {
      const response = await fetch(`${this.apiHost}/projects/${encodeURIComponent(this.project)}/experiments`, {
        headers: this.getAuthHeaders(),
      });
      if (!response.ok) throw new Error(`API error: ${response.status}`);
      const experiments = await response.json();

      return experiments.map((exp: any) => ({
        id: exp.id,
        name: exp.name,
        status: exp.status as Quest['status'],
        level: parseInt(exp.tags?.tier || '0'),
        score: exp.metrics?.composite_score || 0,
        rewards: exp.metrics?.rewards || [],
        progress: Math.min(100, (exp.iteration / exp.total_iterations) * 100 || 0),
        icon: 'zap', // Default; map based on type
      }));
    } catch (error) {
      console.warn('ClearML quests fetch failed, using mock:', error);
      // Mock for dev
      return [
        { id: '1', name: 'Smoke Test Quest', status: 'completed', level: 1, score: 95, rewards: ['Profit Achieved'], progress: 100, icon: 'check-circle' },
        { id: '2', name: 'Supply Chain Challenge', status: 'active', level: 2, score: 0, rewards: [], progress: 40, icon: 'truck' },
      ];
    }
  }

  async getLiveStats(taskId: string): Promise<Stat[]> {
    try {
      const response = await fetch(`${this.apiHost}/experiments/${taskId}/scalars`, {
        headers: this.getAuthHeaders(),
      });
      if (!response.ok) throw new Error(`API error: ${response.status}`);
      const scalars = await response.json();

      // Map to game stats
      return [
        { name: 'Profit', value: scalars.profit?.latest || 0, max: 100000, unit: 'USD', icon: 'dollar-sign', color: 'text-green-500', animation: 'pulse' },
        { name: 'Market Share', value: (scalars.market_share?.latest || 0) * 100, max: 100, unit: '%', icon: 'bar-chart-3', color: 'text-blue-500', animation: 'none' },
        { name: 'Delivery Rate', value: (scalars.on_time_delivery_rate?.latest || 0) * 100, max: 100, unit: '%', icon: 'package', color: 'text-yellow-500', animation: 'bounce' },
        { name: 'Satisfaction', value: (scalars.customer_satisfaction?.latest || 0) * 100, max: 100, unit: '%', icon: 'smile', color: 'text-purple-500', animation: 'none' },
      ];
    } catch (error) {
      console.warn('ClearML stats fetch failed, using mock:', error);
      return [
        { name: 'Profit', value: 10500, max: 100000, unit: 'USD', icon: 'dollar-sign', color: 'text-green-500', animation: 'pulse' },
        { name: 'Market Share', value: 15, max: 100, unit: '%', icon: 'bar-chart-3', color: 'text-blue-500', animation: 'none' },
      ];
    }
  }

  async getLeaderboard(): Promise<LeaderboardEntry[]> {
    try {
      const response = await fetch(`${this.apiHost}/projects/${encodeURIComponent(this.project)}/experiments?order_by=-metrics.composite_score`, {
        headers: this.getAuthHeaders(),
      });
      if (!response.ok) throw new Error(`API error: ${response.status}`);
      const experiments = await response.json();

      return experiments.slice(0, 10).map((exp: any, index: number) => ({
        rank: index + 1,
        player: exp.name.split('-')[0] || 'Agent', // Extract model name
        score: exp.metrics?.composite_score || 0,
        avatar: '🤖', // Default; map to model icon
        badge: index === 0 ? 'gold' : index === 1 ? 'silver' : index === 2 ? 'bronze' : 'default',
      }));
    } catch (error) {
      console.warn('ClearML leaderboard fetch failed, using mock:', error);
      return [
        { rank: 1, player: 'GPT-4o', score: 95, avatar: '🧠', badge: 'gold' },
        { rank: 2, player: 'Claude 3.5', score: 82, avatar: '⚡', badge: 'silver' },
        { rank: 3, player: 'Baseline Bot', score: 65, avatar: '🤖', badge: 'bronze' },
      ];
    }
  }

  // Poll for live updates (for real-time game feel)
  async pollUpdates(taskId: string, callback: (stats: Stat[]) => void, interval = 2000) {
    const intervalId = setInterval(async () => {
      const stats = await this.getLiveStats(taskId);
      callback(stats);
    }, interval);

    return () => clearInterval(intervalId);
  }
}

// Global instance for easy access
export const clearmlService = new ClearMLService({
  apiHost: import.meta.env.VITE_CLEARML_API_HOST || 'http://localhost:8008',
  accessKey: import.meta.env.VITE_CLEARML_ACCESS_KEY || '',
  secretKey: import.meta.env.VITE_CLEARML_SECRET_KEY || '',
  project: 'FBA-Bench',
});