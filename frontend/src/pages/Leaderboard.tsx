import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  TrophyIcon, 
  ChartBarIcon,
  CalendarIcon,
  UserIcon,
  StarIcon
} from '@heroicons/react/24/outline';
import { apiService } from '../services/api';
import { useAppStore } from '../store/appStore';

interface LeaderboardEntry {
  rank: number;
  experimentId: string;
  name: string;
  score: number;
  model: string;
  status: string;
  completedAt: string;
  avatar: string;
  badge: 'gold' | 'silver' | 'bronze' | 'default';
}

const Leaderboard: React.FC = () => {
  const { leaderboard, setLeaderboard, setLoading } = useAppStore();
  const [timeframe, setTimeframe] = useState<'week' | 'month' | 'all'>('all');
  const [category, setCategory] = useState<'overall' | 'profit' | 'efficiency'>('overall');

  useEffect(() => {
    loadLeaderboard();
  }, [timeframe, category]);

  const loadLeaderboard = async () => {
    try {
      setLoading('leaderboard', true);
      const response = await apiService.getLeaderboard(50);
      
      console.log('=== LEADERBOARD DEBUG ===');
      console.log('Leaderboard response raw:', response);
      console.log('Leaderboard response type:', typeof response);
      console.log('Leaderboard response.data:', response?.data);
      console.log('Leaderboard response.data is array?', Array.isArray(response?.data));
      console.log('Leaderboard response structure:', JSON.stringify(response, null, 2));
      
      // Extract data array from API response
      const data = response?.data || [];
      
      // Validate data is array before mapping
      if (!Array.isArray(data)) {
        console.error('Expected array but got:', typeof data, data);
        throw new Error(`Expected array but got ${typeof data}`);
      }
      
      // Transform data to add game elements
      const enhancedData: LeaderboardEntry[] = data.map((entry, index) => ({
        ...entry,
        avatar: getAvatarForModel(entry.model),
        badge: getBadgeForRank(index + 1),
      }));
      
      setLeaderboard(enhancedData);
    } catch (error) {
      console.error('Failed to load leaderboard:', error);
      console.log('Using mock data fallback');
      // Use mock data for demonstration
      setLeaderboard(mockLeaderboardData);
    } finally {
      setLoading('leaderboard', false);
    }
  };

  const getAvatarForModel = (model: string): string => {
    if (model.toLowerCase().includes('gpt')) return '🧠';
    if (model.toLowerCase().includes('claude')) return '⚡';
    if (model.toLowerCase().includes('llama')) return '🦙';
    if (model.toLowerCase().includes('baseline')) return '🤖';
    return '🎯';
  };

  const getBadgeForRank = (rank: number): 'gold' | 'silver' | 'bronze' | 'default' => {
    if (rank === 1) return 'gold';
    if (rank === 2) return 'silver';
    if (rank === 3) return 'bronze';
    return 'default';
  };

  const getBadgeColor = (badge: string) => {
    switch (badge) {
      case 'gold': return 'from-yellow-400 to-orange-400 border-yellow-400/50';
      case 'silver': return 'from-gray-300 to-gray-400 border-gray-400/50';
      case 'bronze': return 'from-orange-400 to-red-400 border-orange-400/50';
      default: return 'from-slate-500 to-slate-600 border-slate-500/50';
    }
  };

  const getRankDisplay = (rank: number) => {
    if (rank === 1) return '🥇';
    if (rank === 2) return '🥈';
    if (rank === 3) return '🥉';
    return `#${rank}`;
  };

  // Mock data for development
  const mockLeaderboardData: LeaderboardEntry[] = [
    {
      rank: 1,
      experimentId: '1',
      name: 'Supply Chain Mastery',
      score: 95.2,
      model: 'GPT-4',
      status: 'completed',
      completedAt: '2024-01-15T10:30:00Z',
      avatar: '🧠',
      badge: 'gold'
    },
    {
      rank: 2,
      experimentId: '2',
      name: 'Market Expansion Quest',
      score: 88.7,
      model: 'Claude-3.5',
      status: 'completed',
      completedAt: '2024-01-14T15:45:00Z',
      avatar: '⚡',
      badge: 'silver'
    },
    {
      rank: 3,
      experimentId: '3',
      name: 'Efficiency Challenge',
      score: 82.1,
      model: 'Llama-3.1',
      status: 'completed',
      completedAt: '2024-01-13T09:20:00Z',
      avatar: '🦙',
      badge: 'bronze'
    },
    {
      rank: 4,
      experimentId: '4',
      name: 'Baseline Performance',
      score: 65.3,
      model: 'Baseline Bot',
      status: 'completed',
      completedAt: '2024-01-12T14:10:00Z',
      avatar: '🤖',
      badge: 'default'
    },
  ];

  const displayData = leaderboard.length > 0 ? leaderboard : mockLeaderboardData;

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center mb-8"
      >
        <h1 className="text-4xl font-bold bg-gradient-to-r from-yellow-400 to-orange-400 bg-clip-text text-transparent mb-4">
          🏆 FBA Empire Leaderboard
        </h1>
        <p className="text-slate-400 text-lg">Top performing business agents and their achievements</p>
      </motion.div>

      {/* Filters */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-slate-800/50 backdrop-blur-sm rounded-xl border border-slate-700/50 p-6 mb-8"
      >
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center space-x-4">
            <div>
              <label className="block text-slate-300 text-sm font-medium mb-2">Timeframe</label>
              <select
                value={timeframe}
                onChange={(e) => setTimeframe(e.target.value as any)}
                className="px-3 py-2 bg-slate-700/50 border border-slate-600/50 rounded-lg text-white focus:border-violet-500 focus:outline-none"
              >
                <option value="week">This Week</option>
                <option value="month">This Month</option>
                <option value="all">All Time</option>
              </select>
            </div>
            
            <div>
              <label className="block text-slate-300 text-sm font-medium mb-2">Category</label>
              <select
                value={category}
                onChange={(e) => setCategory(e.target.value as any)}
                className="px-3 py-2 bg-slate-700/50 border border-slate-600/50 rounded-lg text-white focus:border-violet-500 focus:outline-none"
              >
                <option value="overall">Overall Score</option>
                <option value="profit">Profit Performance</option>
                <option value="efficiency">Efficiency Rating</option>
              </select>
            </div>
          </div>
          
          <div className="text-right">
            <p className="text-slate-400 text-sm">Last updated</p>
            <p className="text-white">{new Date().toLocaleTimeString()}</p>
          </div>
        </div>
      </motion.div>

      {/* Leaderboard */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="space-y-4"
      >
        {displayData.map((entry, index) => (
          <motion.div
            key={entry.experimentId}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.05 }}
            className={`bg-slate-800/50 backdrop-blur-sm rounded-xl border p-6 hover:border-slate-600/50 transition-all duration-200 ${
              entry.rank <= 3 ? 'border-yellow-400/30 bg-gradient-to-r from-yellow-400/5 to-transparent' : 'border-slate-700/50'
            }`}
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-6">
                {/* Rank */}
                <motion.div
                  className={`flex items-center justify-center w-16 h-16 rounded-full bg-gradient-to-br ${getBadgeColor(entry.badge)} border-2 font-bold text-xl`}
                  whileHover={{ scale: 1.1 }}
                >
                  {getRankDisplay(entry.rank)}
                </motion.div>
                
                {/* Experiment Info */}
                <div>
                  <div className="flex items-center space-x-3 mb-2">
                    <span className="text-2xl">{entry.avatar}</span>
                    <div>
                      <h3 className="text-white font-semibold text-lg">{entry.name}</h3>
                      <p className="text-slate-400">{entry.model}</p>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-4 text-sm text-slate-400">
                    <div className="flex items-center space-x-1">
                      <CalendarIcon className="h-4 w-4" />
                      <span>{new Date(entry.completedAt).toLocaleDateString()}</span>
                    </div>
                    <div className="flex items-center space-x-1">
                      <ChartBarIcon className="h-4 w-4" />
                      <span>{entry.status}</span>
                    </div>
                  </div>
                </div>
              </div>
              
              {/* Score */}
              <div className="text-right">
                <motion.div
                  className="text-3xl font-bold bg-gradient-to-r from-green-400 to-blue-400 bg-clip-text text-transparent"
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ delay: index * 0.1, type: 'spring', stiffness: 200 }}
                >
                  {entry.score.toFixed(1)}
                </motion.div>
                <p className="text-slate-400 text-sm">points</p>
                
                {/* Achievement Stars */}
                <div className="flex justify-end mt-2">
                  {Array.from({ length: 5 }).map((_, i) => (
                    <StarIcon
                      key={i}
                      className={`h-4 w-4 ${
                        i < Math.floor(entry.score / 20) 
                          ? 'text-yellow-400 fill-yellow-400' 
                          : 'text-slate-600'
                      }`}
                    />
                  ))}
                </div>
              </div>
            </div>
            
            {/* Hover Actions */}
            <motion.div
              className="mt-4 pt-4 border-t border-slate-700/50 flex items-center justify-between"
              initial={{ opacity: 0 }}
              whileHover={{ opacity: 1 }}
            >
              <div className="flex space-x-2">
                <button className="px-3 py-1 bg-violet-500/20 text-violet-300 rounded-lg text-sm hover:bg-violet-500/30 transition-colors">
                  View Details
                </button>
                <button className="px-3 py-1 bg-blue-500/20 text-blue-300 rounded-lg text-sm hover:bg-blue-500/30 transition-colors">
                  Clone Strategy
                </button>
              </div>
              
              <div className="text-slate-400 text-sm">
                Click to explore this champion's strategy
              </div>
            </motion.div>
          </motion.div>
        ))}
      </motion.div>

      {/* Achievement Gallery */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="mt-12 bg-slate-800/50 backdrop-blur-sm rounded-xl border border-slate-700/50 p-6"
      >
        <h2 className="text-xl font-semibold text-white mb-6 flex items-center">
          <StarIcon className="h-5 w-5 mr-2 text-yellow-400" />
          Achievement Gallery
        </h2>
        
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            { title: 'Profit Master', description: 'Exceed $50K profit', icon: '💰', unlocked: true },
            { title: 'Market Dominator', description: '25% market share', icon: '📊', unlocked: true },
            { title: 'Customer Champion', description: '95% satisfaction', icon: '😊', unlocked: false },
            { title: 'Speed Demon', description: '99% delivery rate', icon: '🚚', unlocked: false },
          ].map((achievement, index) => (
            <motion.div
              key={achievement.title}
              className={`p-4 rounded-lg border text-center ${
                achievement.unlocked 
                  ? 'bg-gradient-to-br from-yellow-400/10 to-orange-400/10 border-yellow-400/30' 
                  : 'bg-slate-700/30 border-slate-600/30'
              }`}
              whileHover={{ scale: 1.05 }}
            >
              <div className={`text-2xl mb-2 ${achievement.unlocked ? '' : 'grayscale opacity-50'}`}>
                {achievement.icon}
              </div>
              <h4 className={`font-semibold mb-1 ${achievement.unlocked ? 'text-yellow-300' : 'text-slate-400'}`}>
                {achievement.title}
              </h4>
              <p className="text-xs text-slate-400">{achievement.description}</p>
            </motion.div>
          ))}
        </div>
      </motion.div>
    </div>
  );
};

// Mock data for development
const mockLeaderboardData: LeaderboardEntry[] = [
  {
    rank: 1,
    experimentId: '1',
    name: '🎮 Quest: Supply Chain Mastery - Level 3',
    score: 95.2,
    model: 'GPT-4 Turbo',
    status: 'completed',
    completedAt: '2024-01-15T10:30:00Z',
    avatar: '🧠',
    badge: 'gold'
  },
  {
    rank: 2,
    experimentId: '2',
    name: '🎮 Quest: Market Expansion - Level 2',
    score: 88.7,
    model: 'Claude-3.5 Sonnet',
    status: 'completed',
    completedAt: '2024-01-14T15:45:00Z',
    avatar: '⚡',
    badge: 'silver'
  },
  {
    rank: 3,
    experimentId: '3',
    name: '🎮 Quest: International Trade - Level 2',
    score: 82.1,
    model: 'Llama-3.1-405B',
    status: 'completed',
    completedAt: '2024-01-13T09:20:00Z',
    avatar: '🦙',
    badge: 'bronze'
  },
];

export default Leaderboard;