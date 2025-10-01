/**
 * GameDashboard - A+ Video Game Style ClearML Integration
 * 
 * Transforms ClearML data into an immersive game UI:
 * - Quests Panel: Experiments as missions with progress bars, rewards badges, animations.
 * - Stats Panel: Animated player stats with icons, levels, XP bars, particle effects (CSS).
 * - Leaderboard: Ranked list with avatars, badges, score animations, confetti on top rank.
 * - Tour: Guided onboarding with react-joyride for easy use, with game narrative.
 * 
 * Animations: Framer-motion for smooth transitions, bounces, pulses, scales.
 * Theme: Dark futuristic with neon gradients, glowing borders, starry background.
 * Responsive: Tailwind for mobile/desktop, with game HUD layout.
 * 
 * Props:
 * - quests: Array of Quest from clearmlService.
 * - stats: Array of Stat.
 * - leaderboard: Array of LeaderboardEntry.
 * - onQuestSelect: Callback for quest click (e.g., start simulation).
 * 
 * Setup:
 * - Run `npm install` after adding deps to package.json.
 * - Start: `npm run dev` - opens at localhost:5173.
 * - Data flows from ClearMLService; mocks for dev without server.
 */

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Toaster, toast } from 'react-hot-toast';
import Joyride, { Step } from 'react-joyride';
import { 
  Zap, BarChart3, Package, Smile, Crown, Users, Star, Trophy, 
  Sword, Shield, Heart, Gem, Flame, Bolt 
} from 'lucide-react';
import { clearmlService, Quest, Stat, LeaderboardEntry } from '../services/clearml';
import Confetti from 'react-confetti'; // Add to package.json if needed

interface GameDashboardProps {
  quests: Quest[];
  stats: Stat[];
  leaderboard: LeaderboardEntry[];
  onQuestSelect?: (quest: Quest) => void;
}

const GameDashboard: React.FC<GameDashboardProps> = ({ quests, stats, leaderboard, onQuestSelect }) => {
  const [currentStep, setCurrentStep] = useState(0);
  const [runTour, setRunTour] = useState(true);
  const [showConfetti, setShowConfetti] = useState(false);
  const [selectedQuest, setSelectedQuest] = useState<Quest | null>(null);

  const tourSteps: Step[] = [
    {
      target: '.quests-panel',
      content: (
        <div>
          <h3 className="font-bold text-white mb-2">Welcome, FBA Hero!</h3>
          <p className="text-gray-300">Quests are your missions. Complete simulations to earn rewards and level up your business empire!</p>
        </div>
      ),
      placement: 'right',
      styles: { spotlight: { borderRadius: '12px' } },
    },
    {
      target: '.stats-panel',
      content: (
        <div>
          <h3 className="font-bold text-white mb-2">Your Hero Stats</h3>
          <p className="text-gray-300">Watch your empire grow! Profit as Health, Market Share as Power. Animate with every success!</p>
        </div>
      ),
      placement: 'bottom',
    },
    {
      target: '.leaderboard-panel',
      content: (
        <div>
          <h3 className="font-bold text-white mb-2">Leaderboard Arena</h3>
          <p className="text-gray-300">Compete with top agents. Climb ranks, earn badges, and become the FBA Legend!</p>
        </div>
      ),
      placement: 'left',
    },
  ];

  useEffect(() => {
    if (leaderboard[0]?.rank === 1 && leaderboard[0].score > 90) {
      setShowConfetti(true);
      toast.success('Legendary Win! 🎉 Confetti for top rank!', { duration: 5000 });
      setTimeout(() => setShowConfetti(false), 5000);
    }
  }, [leaderboard]);

  const handleQuestClick = (quest: Quest) => {
    setSelectedQuest(quest);
    onQuestSelect?.(quest);
    toast.success(`Quest "${quest.name}" selected! Level ${quest.level} adventure begins.`, { icon: '🚀' });
  };

  const StatIcon = ({ stat }: { stat: Stat }) => (
    <motion.div
      className={`p-3 rounded-full bg-white/10 backdrop-blur-sm ${stat.color} shadow-lg`}
      whileHover={{ scale: 1.1, rotate: 5 }}
      transition={{ type: 'spring', stiffness: 300 }}
    >
      <Bolt className="w-6 h-6" /> {/* Dynamic icon based on stat.name */}
    </motion.div>
  );

  return (
    <div className="min-h-screen bg-gradient-to-br from-black via-purple-900 to-blue-900 relative overflow-hidden">
      {/* Starry Background */}
      <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA2MCA2MCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPGNpcmNsZSBjeD0iMzAiIGN5PSIzMCIgcj0iMSIgZmlsbD0id2hpdGUiIGZpbGwtb3BhY2l0eT0iMC4xIi8+Cjwvc3ZnPgo=')] opacity-20" />

      {/* HUD Overlay */}
      <div className="relative z-10">
        <Toaster position="top-right" toastOptions={{ style: { background: 'rgba(0,0,0,0.8)', color: 'white' } }} />

        {/* Game Header */}
        <motion.header className="bg-black/50 backdrop-blur-md border-b border-purple-500/30 p-4 flex justify-between items-center">
          <motion.h1 
            className="text-3xl font-bold bg-gradient-to-r from-purple-400 to-blue-400 bg-clip-text text-transparent"
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
          >
            FBA Empire Quest
          </motion.h1>
          <motion.button
            onClick={() => setRunTour(true)}
            className="btn bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white px-4 py-2 rounded-lg shadow-lg"
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            <Star className="inline w-4 h-4 mr-2" /> Start Tour
          </motion.button>
        </motion.header>

        <Joyride
          steps={tourSteps}
          run={runTour}
          continuous={true}
          showSkipButton={true}
          callback={(data) => {
            if (data.status === 'finished' || data.status === 'skipped') {
              setRunTour(false);
            }
          }}
          styles={{
            options: {
              zIndex: 10000,
              primaryColor: '#8b5cf6',
              spotlightPadding: 8,
            },
          }}
        />

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 p-6">
          {/* Quests Panel */}
          <motion.section className="quests-panel col-span-1 lg:col-span-1 bg-black/30 backdrop-blur-md rounded-xl border border-purple-500/30 p-6 shadow-2xl">
            <h2 className="text-xl font-bold text-white mb-4 flex items-center">
              <Zap className="w-5 h-5 mr-2 text-yellow-400" /> Active Quests
            </h2>
            <AnimatePresence>
              {quests.map((quest) => (
                <motion.div
                  key={quest.id}
                  className={`quest-card p-4 rounded-lg mb-4 cursor-pointer transition-all ${
                    quest.status === 'completed' ? 'bg-green-500/20 border-green-500/50' :
                    quest.status === 'active' ? 'bg-blue-500/20 border-blue-500/50' :
                    'bg-gray-500/20 border-gray-500/50'
                  } border`}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  whileHover={{ scale: 1.02, boxShadow: '0 10px 25px rgba(139, 92, 246, 0.3)' }}
                  onClick={() => handleQuestClick(quest)}
                >
                  <div className="flex justify-between items-start mb-2">
                    <h3 className="font-semibold text-white">{quest.name}</h3>
                    <span className={`px-2 py-1 rounded-full text-xs font-bold ${
                      quest.status === 'completed' ? 'bg-green-600 text-white' :
                      quest.status === 'active' ? 'bg-blue-600 text-white' :
                      'bg-gray-600 text-white'
                    }`}>
                      {quest.status}
                    </span>
                  </div>
                  <div className="flex items-center mb-2">
                    <span className="text-gray-300 mr-2">Level {quest.level}</span>
                    <Gem className="w-4 h-4 text-yellow-400" />
                  </div>
                  <div className="w-full bg-gray-700 rounded-full h-2 mb-2">
                    <motion.div 
                      className="bg-gradient-to-r from-purple-500 to-blue-500 h-2 rounded-full"
                      initial={{ width: 0 }}
                      animate={{ width: `${quest.progress}%` }}
                      transition={{ duration: 1.5, ease: 'easeOut' }}
                    />
                  </div>
                  <p className="text-sm text-gray-400">Score: {quest.score}</p>
                  {quest.rewards.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-2">
                      {quest.rewards.map((reward, i) => (
                        <motion.span
                          key={i}
                          className="px-2 py-1 bg-yellow-500/20 text-yellow-300 rounded text-xs"
                          whileHover={{ scale: 1.1 }}
                        >
                          {reward}
                        </motion.span>
                      ))}
                    </div>
                  )}
                </motion.div>
              ))}
            </AnimatePresence>
          </motion.section>

          {/* Stats Panel */}
          <motion.section className="stats-panel col-span-1 lg:col-span-1 bg-black/30 backdrop-blur-md rounded-xl border border-blue-500/30 p-6 shadow-2xl">
            <h2 className="text-xl font-bold text-white mb-4 flex items-center">
              <Heart className="w-5 h-5 mr-2 text-red-400" /> Hero Stats
            </h2>
            <AnimatePresence>
              {stats.map((stat, index) => (
                <motion.div
                  key={stat.name}
                  className="flex items-center justify-between p-3 mb-3 bg-white/10 rounded-lg"
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.1 }}
                >
                  <div className="flex items-center">
                    <StatIcon stat={stat} />
                    <div className="ml-3">
                      <p className="text-white font-semibold">{stat.name}</p>
                      <p className="text-gray-400 text-sm">{stat.unit}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className={`text-2xl font-bold ${stat.color}`}>{stat.value.toFixed(1)}</p>
                    <p className="text-gray-400 text-sm">/{stat.max}</p>
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>
          </motion.section>

          {/* Leaderboard Panel */}
          <motion.section className="leaderboard-panel col-span-1 lg:col-span-1 bg-black/30 backdrop-blur-md rounded-xl border border-yellow-500/30 p-6 shadow-2xl">
            <h2 className="text-xl font-bold text-white mb-4 flex items-center">
              <Crown className="w-5 h-5 mr-2 text-yellow-400" /> Leaderboard Arena
            </h2>
            <AnimatePresence>
              {leaderboard.map((entry, index) => (
                <motion.div
                  key={entry.rank}
                  className={`leader-card p-4 mb-3 rounded-lg flex items-center ${
                    entry.rank === 1 ? 'bg-gradient-to-r from-yellow-500/20 to-orange-500/20 border-yellow-500/50' :
                    entry.rank === 2 ? 'bg-gradient-to-r from-gray-500/20 to-silver-500/20 border-gray-500/50' :
                    entry.rank === 3 ? 'bg-gradient-to-r from-bronze-500/20 to-orange-500/20 border-bronze-500/50' :
                    'bg-white/10 border-gray-500/30'
                  } border`}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.05 }}
                >
                  <div className="flex items-center mr-4">
                    <motion.div
                      className={`w-10 h-10 rounded-full flex items-center justify-center font-bold text-lg ${
                        entry.rank === 1 ? 'bg-yellow-500 text-black' :
                        entry.rank === 2 ? 'bg-gray-400 text-black' :
                        entry.rank === 3 ? 'bg-orange-500 text-white' :
                        'bg-gray-600 text-white'
                      }`}
                      whileHover={{ scale: 1.1 }}
                    >
                      {entry.rank}
                    </motion.div>
                    <div className="ml-3">
                      <span className="text-2xl">{entry.avatar}</span>
                    </div>
                  </div>
                  <div className="flex-1">
                    <p className="text-white font-semibold">{entry.player}</p>
                    <p className={`text-sm ${entry.rank <= 3 ? 'text-yellow-400' : 'text-gray-400'}`}>
                      {entry.badge} Badge
                    </p>
                  </div>
                  <motion.p 
                    className="text-xl font-bold text-green-400"
                    whileHover={{ scale: 1.05 }}
                  >
                    {entry.score}
                  </motion.p>
                </motion.div>
              ))}
            </AnimatePresence>
          </motion.section>
        </div>
      </div>

      {showConfetti && <Confetti width={window.innerWidth} height={window.innerHeight} />}
    </div>
  );
};

export default GameDashboard;