import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  HomeIcon,
  BeakerIcon,
  DocumentTextIcon,
  TrophyIcon,
  CogIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline';

interface NavigationProps {
  apiConnected: boolean;
  clearmlConnected: boolean;
}

const Navigation: React.FC<NavigationProps> = ({ apiConnected, clearmlConnected }) => {
  const location = useLocation();

  const navItems = [
    { path: '/dashboard', label: 'Dashboard', icon: HomeIcon },
    { path: '/experiments', label: 'Experiments', icon: BeakerIcon },
    { path: '/templates', label: 'Templates', icon: DocumentTextIcon },
    { path: '/leaderboard', label: 'Leaderboard', icon: TrophyIcon },
    { path: '/medusa-logs', label: 'Medusa Logs', icon: BeakerIcon },
    { path: '/settings', label: 'Settings', icon: CogIcon },
  ];

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-white border-b border-gray-200 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo and Brand */}
          <motion.div
            className="flex items-center space-x-3"
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5 }}
          >
            <div className="h-8 w-8 bg-blue-600 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-sm">FBA</span>
            </div>
            <div>
              <h1 className="text-xl font-bold text-gray-900">
                FBA-Bench
              </h1>
              <p className="text-xs text-gray-500">Business Agent Simulation Platform</p>
            </div>
          </motion.div>

          {/* Navigation Links */}
          <div className="hidden md:flex items-center space-x-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const navClass = `nav-link ${item.path === '/leaderboard' ? 'nav-leaderboard' : ''} ${item.path === '/medusa-logs' ? 'nav-medusa-logs' : ''}`;
              
              return (
                <NavLink
                  key={item.path}
                  to={item.path}
                  className={({ isActive }) =>
                    `${navClass} relative px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                      isActive
                        ? 'text-blue-600 bg-blue-50 border-b-2 border-blue-600'
                        : 'text-gray-700 hover:text-blue-600 hover:bg-gray-50'
                    }`
                  }
                >
                  <div className="flex items-center space-x-2">
                    <Icon data-testid="nav-icon" className="h-4 w-4" />
                    <span>{item.label}</span>
                  </div>
                </NavLink>
              );
            })}
          </div>

          {/* Status Indicators */}
          <motion.div
            className="flex items-center space-x-4"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
          >
            {/* API Status */}
            <div className="flex items-center space-x-2">
              {apiConnected ? (
                <CheckCircleIcon className="h-5 w-5 text-green-500" />
              ) : (
                <ExclamationTriangleIcon className="h-5 w-5 text-red-500" />
              )}
              <span className="text-sm text-gray-700">API</span>
            </div>

            {/* ClearML Status */}
            <div className="flex items-center space-x-2">
              {clearmlConnected ? (
                <CheckCircleIcon className="h-5 w-5 text-green-500" />
              ) : (
                <ExclamationTriangleIcon className="h-5 w-5 text-orange-500" />
              )}
              <span className="text-sm text-gray-700">ClearML</span>
            </div>
          </motion.div>
        </div>
      </div>
    </nav>
  );
};

export default Navigation;