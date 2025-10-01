import React from 'react';
import { motion } from 'framer-motion';
import { BoltIcon } from '@heroicons/react/24/outline';

const LoadingScreen: React.FC = () => {
  return (
    <div data-testid="loading-container" className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center">
      <motion.div
        className="text-center"
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.5 }}
      >
        {/* Animated Logo */}
        <motion.div
          data-testid="logo-container"
          className="relative mb-8"
          animate={{
            rotate: [0, 360],
            scale: [1, 1.1, 1]
          }}
          transition={{
            rotate: {
              duration: 4,
              repeat: Infinity,
              ease: "linear"
            },
            scale: {
              duration: 2,
              repeat: Infinity,
              ease: "easeInOut"
            }
          }}
        >
          <div className="w-20 h-20 mx-auto bg-gradient-to-br from-violet-400 to-purple-500 rounded-full flex items-center justify-center shadow-2xl">
            <BoltIcon className="h-10 w-10 text-white" />
          </div>
          
          {/* Orbital Rings */}
          <motion.div
            className="absolute inset-0 border-2 border-violet-400/30 rounded-full"
            animate={{ rotate: [0, -360] }}
            transition={{ duration: 6, repeat: Infinity, ease: "linear" }}
          />
          <motion.div
            className="absolute inset-[-8px] border border-purple-400/20 rounded-full"
            animate={{ rotate: [0, 360] }}
            transition={{ duration: 8, repeat: Infinity, ease: "linear" }}
          />
        </motion.div>

        {/* Loading Text */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.2 }}
        >
          <h2 className="text-2xl font-bold bg-gradient-to-r from-violet-400 to-purple-400 bg-clip-text text-transparent mb-4">
            FBA-Bench Dashboard
          </h2>
          
          <motion.p
            className="text-slate-300 mb-6"
            animate={{ opacity: [0.5, 1, 0.5] }}
            transition={{ duration: 2, repeat: Infinity }}
          >
            Initializing business simulation platform...
          </motion.p>

          {/* Progress Dots */}
          <div className="flex justify-center space-x-2">
            {[0, 1, 2].map((i) => (
              <motion.div
                key={i}
                data-testid="progress-dot"
                className="w-3 h-3 bg-violet-400 rounded-full"
                animate={{
                  scale: [1, 1.5, 1],
                  opacity: [0.5, 1, 0.5],
                }}
                transition={{
                  duration: 1.5,
                  repeat: Infinity,
                  delay: i * 0.2,
                }}
              />
            ))}
          </div>
        </motion.div>
      </motion.div>
    </div>
  );
};

export default LoadingScreen;