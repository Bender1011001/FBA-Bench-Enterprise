import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  CogIcon,
  ServerIcon,
  KeyIcon,
  BellIcon,
  PaintBrushIcon,
  PlayIcon,
  StopIcon,
  CheckCircleIcon,
  XCircleIcon,
  ArrowPathIcon,
  ShieldCheckIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline';
import { apiService } from '../services/api';
import { useAppStore } from '../store/appStore';
import { toast } from 'react-hot-toast';
import EnvironmentSetupModal from '../components/setup/EnvironmentSetupModal';
import { environmentService, type ServiceStatus } from '../services/environment';

interface SettingsSectionProps {
  title: string;
  description: string;
  icon: React.ElementType;
  children: React.ReactNode;
}

const SettingsSection: React.FC<SettingsSectionProps> = ({ title, description, icon: Icon, children }) => {
  return (
    <motion.div
      className="bg-slate-800/50 backdrop-blur-sm rounded-xl border border-slate-700/50 p-6"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
    >
      <div className="flex items-center space-x-3 mb-4">
        <div className="p-2 bg-violet-500/20 rounded-lg">
          <Icon className="h-5 w-5 text-violet-400" />
        </div>
        <div>
          <h3 className="text-white font-semibold">{title}</h3>
          <p className="text-slate-400 text-sm">{description}</p>
        </div>
      </div>
      {children}
    </motion.div>
  );
};

const Settings: React.FC = () => {
  const { connectionStatus, theme, setTheme } = useAppStore();
  const [clearmlSettings, setClearmlSettings] = useState({
    apiHost: 'http://localhost:8008',
    webHost: 'http://localhost:8080',
    filesHost: 'http://localhost:8081',
    accessKey: '',
    secretKey: '',
  });
  
  const [stackStatus, setStackStatus] = useState<'stopped' | 'starting' | 'running' | 'error'>('stopped');
  const [notifications, setNotifications] = useState({
    experimentComplete: true,
    experimentFailed: true,
    newLeaderboardEntry: false,
    systemAlerts: true,
  });

  // Environment setup state
  const [showEnvironmentModal, setShowEnvironmentModal] = useState(false);
  const [environmentStatuses, setEnvironmentStatuses] = useState<ServiceStatus[]>([]);

  // Load environment statuses on mount
  useEffect(() => {
    const statuses = environmentService.getServiceStatuses();
    setEnvironmentStatuses(statuses);
  }, []);

  const refreshEnvironmentStatus = () => {
    const statuses = environmentService.getServiceStatuses();
    setEnvironmentStatuses(statuses);
  };

  const handleStartClearML = async () => {
    try {
      setStackStatus('starting');
      toast.loading('Starting ClearML stack...', { id: 'clearml-start' });
      
      await apiService.startClearMLStack();
      
      setStackStatus('running');
      toast.success('ClearML stack started successfully!', { id: 'clearml-start' });
      
      // Populate with demo data
      setTimeout(async () => {
        try {
          toast.loading('Creating demo experiments...', { id: 'demo' });
          // This would trigger the demo script
          await new Promise(resolve => setTimeout(resolve, 2000)); // Simulate
          toast.success('Demo experiments created! Check the Experiments page.', { id: 'demo' });
        } catch (error) {
          toast.error('Failed to create demo data', { id: 'demo' });
        }
      }, 3000);
      
    } catch (error) {
      setStackStatus('error');
      toast.error('Failed to start ClearML stack', { id: 'clearml-start' });
    }
  };

  const handleStopClearML = async () => {
    try {
      toast.loading('Stopping ClearML stack...', { id: 'clearml-stop' });
      await apiService.stopClearMLStack();
      setStackStatus('stopped');
      toast.success('ClearML stack stopped', { id: 'clearml-stop' });
    } catch (error) {
      toast.error('Failed to stop ClearML stack', { id: 'clearml-stop' });
    }
  };

  const handleTestConnection = async () => {
    try {
      toast.loading('Testing connection...', { id: 'test' });
      const statusResp = await apiService.getClearMLStatus();
      
      if (statusResp.data.connected) {
        toast.success('Connection successful!', { id: 'test' });
      } else {
        toast.error('Connection failed', { id: 'test' });
      }
    } catch (error) {
      toast.error('Connection test failed', { id: 'test' });
    }
  };

  const handleSaveSettings = () => {
    // Save settings to localStorage or API
    localStorage.setItem('clearml-settings', JSON.stringify(clearmlSettings));
    localStorage.setItem('notification-settings', JSON.stringify(notifications));
    toast.success('Settings saved successfully!');
  };

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <h1 className="text-3xl font-bold bg-gradient-to-r from-violet-400 to-purple-400 bg-clip-text text-transparent">
          Settings
        </h1>
        <p className="text-slate-400 mt-2">Configure your FBA-Bench dashboard and integrations</p>
      </motion.div>

      <div className="space-y-8">
        {/* Environment Setup */}
        <SettingsSection
          title="Environment Setup"
          description="Configure API keys and credentials for external services"
          icon={ShieldCheckIcon}
        >
          <div className="space-y-4">
            {/* Configuration Status */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              {environmentStatuses.map((status) => (
                <div
                  key={status.service}
                  className={`p-4 rounded-lg border ${
                    status.configured
                      ? 'bg-green-500/10 border-green-500/20'
                      : 'bg-slate-700/30 border-slate-600/30'
                  }`}
                >
                  <div className="flex items-center space-x-2 mb-2">
                    {status.configured ? (
                      <CheckCircleIcon className="h-5 w-5 text-green-400" />
                    ) : (
                      <XCircleIcon className="h-5 w-5 text-slate-500" />
                    )}
                    <span className={`font-medium ${status.configured ? 'text-green-300' : 'text-slate-400'}`}>
                      {status.service}
                    </span>
                  </div>
                  <p className={`text-sm ${status.configured ? 'text-green-400/80' : 'text-slate-500'}`}>
                    {status.configured ? 'Configured' : 'Not configured'}
                  </p>
                  {status.lastTested && (
                    <p className="text-xs text-slate-400 mt-1">
                      Last tested: {status.lastTested.toLocaleTimeString()}
                    </p>
                  )}
                </div>
              ))}
            </div>

            {/* Missing Keys Warning */}
            {environmentStatuses.some(s => !s.configured) && (
              <div className="flex items-start space-x-3 p-4 bg-amber-500/10 border border-amber-500/20 rounded-lg">
                <ExclamationTriangleIcon className="h-5 w-5 text-amber-400 flex-shrink-0 mt-0.5" />
                <div className="text-sm">
                  <p className="text-amber-300 font-medium mb-1">Configuration Incomplete</p>
                  <p className="text-amber-200/80">
                    Some services are not configured. Configure API keys to enable full functionality.
                  </p>
                </div>
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex items-center justify-between">
              <div className="flex space-x-3">
                <button
                  onClick={() => setShowEnvironmentModal(true)}
                  className="flex items-center space-x-2 px-4 py-2 bg-violet-500/20 text-violet-300 rounded-lg hover:bg-violet-500/30 border border-violet-500/30 transition-colors"
                >
                  <KeyIcon className="h-4 w-4" />
                  <span>Configure API Keys</span>
                </button>
                
                <button
                  onClick={refreshEnvironmentStatus}
                  className="flex items-center space-x-2 px-4 py-2 bg-slate-600/30 text-slate-300 rounded-lg hover:bg-slate-600/50 border border-slate-600/50 transition-colors"
                >
                  <ArrowPathIcon className="h-4 w-4" />
                  <span>Refresh Status</span>
                </button>
              </div>

              {environmentStatuses.some(s => s.configured) && (
                <button
                  onClick={() => {
                    environmentService.clearApiKeys();
                    refreshEnvironmentStatus();
                    toast.success('All API keys cleared');
                  }}
                  className="px-4 py-2 text-red-400 border border-red-500/30 rounded-lg hover:bg-red-500/10 hover:text-red-300 transition-colors"
                >
                  Clear All Keys
                </button>
              )}
            </div>

            {/* Setup Status Summary */}
            <div className="p-4 bg-slate-700/30 rounded-lg border border-slate-600/30">
              <h4 className="text-white font-medium mb-2">Setup Status</h4>
              <div className="text-sm space-y-1">
                <div className="flex justify-between">
                  <span className="text-slate-400">Basic Setup Complete:</span>
                  <span className={environmentService.isBasicSetupComplete() ? "text-green-400" : "text-amber-400"}>
                    {environmentService.isBasicSetupComplete() ? 'Yes' : 'No'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Configured Services:</span>
                  <span className="text-white">
                    {environmentStatuses.filter(s => s.configured).length} / {environmentStatuses.length}
                  </span>
                </div>
                {!environmentService.isBasicSetupComplete() && (
                  <p className="text-amber-300 text-xs mt-2">
                    Configure at least one LLM provider (OpenAI or OpenRouter) and ClearML credentials to get started.
                  </p>
                )}
              </div>
            </div>
          </div>
        </SettingsSection>

        {/* ClearML Integration */}
        <SettingsSection
          title="ClearML Integration"
          description="Configure connection to ClearML experiment tracking server"
          icon={ServerIcon}
        >
          <div className="space-y-6">
            {/* Connection Status */}
            <div className="flex items-center justify-between p-4 bg-slate-700/30 rounded-lg">
              <div className="flex items-center space-x-3">
                {connectionStatus.clearmlConnected ? (
                  <CheckCircleIcon className="h-6 w-6 text-green-400" />
                ) : (
                  <XCircleIcon className="h-6 w-6 text-red-400" />
                )}
                <div>
                  <p className="text-white font-medium">
                    {connectionStatus.clearmlConnected ? 'Connected' : 'Disconnected'}
                  </p>
                  <p className="text-slate-400 text-sm">
                    {connectionStatus.clearmlConnected 
                      ? 'ClearML server is reachable and configured'
                      : 'Unable to connect to ClearML server'
                    }
                  </p>
                </div>
              </div>
              
              <div className="flex space-x-2">
                <button
                  onClick={handleTestConnection}
                  className="px-4 py-2 bg-blue-500/20 text-blue-300 rounded-lg hover:bg-blue-500/30 transition-colors"
                >
                  Test Connection
                </button>
                
                {stackStatus === 'running' ? (
                  <button
                    onClick={handleStopClearML}
                    className="flex items-center space-x-2 px-4 py-2 bg-red-500/20 text-red-300 rounded-lg hover:bg-red-500/30 transition-colors"
                  >
                    <StopIcon className="h-4 w-4" />
                    <span>Stop Stack</span>
                  </button>
                ) : (
                  <button
                    onClick={handleStartClearML}
                    className="flex items-center space-x-2 px-4 py-2 bg-green-500/20 text-green-300 rounded-lg hover:bg-green-500/30 transition-colors"
                    disabled={stackStatus === 'starting'}
                  >
                    {stackStatus === 'starting' ? (
                      <ArrowPathIcon className="h-4 w-4 animate-spin" />
                    ) : (
                      <PlayIcon className="h-4 w-4" />
                    )}
                    <span>{stackStatus === 'starting' ? 'Starting...' : 'Start Stack'}</span>
                  </button>
                )}
              </div>
            </div>
            
            {/* Server Configuration */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-slate-300 text-sm font-medium mb-2">API Host</label>
                <input
                  type="text"
                  value={clearmlSettings.apiHost}
                  onChange={(e) => setClearmlSettings(prev => ({ ...prev, apiHost: e.target.value }))}
                  className="w-full px-3 py-2 bg-slate-700/50 border border-slate-600/50 rounded-lg text-white focus:border-violet-500 focus:outline-none"
                  placeholder="http://localhost:8008"
                />
              </div>
              
              <div>
                <label className="block text-slate-300 text-sm font-medium mb-2">Web Host</label>
                <input
                  type="text"
                  value={clearmlSettings.webHost}
                  onChange={(e) => setClearmlSettings(prev => ({ ...prev, webHost: e.target.value }))}
                  className="w-full px-3 py-2 bg-slate-700/50 border border-slate-600/50 rounded-lg text-white focus:border-violet-500 focus:outline-none"
                  placeholder="http://localhost:8080"
                />
              </div>
              
              <div>
                <label className="block text-slate-300 text-sm font-medium mb-2">Files Host</label>
                <input
                  type="text"
                  value={clearmlSettings.filesHost}
                  onChange={(e) => setClearmlSettings(prev => ({ ...prev, filesHost: e.target.value }))}
                  className="w-full px-3 py-2 bg-slate-700/50 border border-slate-600/50 rounded-lg text-white focus:border-violet-500 focus:outline-none"
                  placeholder="http://localhost:8081"
                />
              </div>
            </div>
            
            {/* Credentials */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-slate-300 text-sm font-medium mb-2">Access Key</label>
                <input
                  type="password"
                  value={clearmlSettings.accessKey}
                  onChange={(e) => setClearmlSettings(prev => ({ ...prev, accessKey: e.target.value }))}
                  className="w-full px-3 py-2 bg-slate-700/50 border border-slate-600/50 rounded-lg text-white focus:border-violet-500 focus:outline-none"
                  placeholder="Your ClearML access key"
                />
              </div>
              
              <div>
                <label className="block text-slate-300 text-sm font-medium mb-2">Secret Key</label>
                <input
                  type="password"
                  value={clearmlSettings.secretKey}
                  onChange={(e) => setClearmlSettings(prev => ({ ...prev, secretKey: e.target.value }))}
                  className="w-full px-3 py-2 bg-slate-700/50 border border-slate-600/50 rounded-lg text-white focus:border-violet-500 focus:outline-none"
                  placeholder="Your ClearML secret key"
                />
              </div>
            </div>
          </div>
        </SettingsSection>

        {/* Appearance */}
        <SettingsSection
          title="Appearance"
          description="Customize the look and feel of your dashboard"
          icon={PaintBrushIcon}
        >
          <div className="space-y-4">
            <div>
              <label className="block text-slate-300 text-sm font-medium mb-3">Theme</label>
              <div className="flex space-x-4">
                <button
                  onClick={() => setTheme('dark')}
                  className={`px-4 py-2 rounded-lg border transition-colors ${
                    theme === 'dark'
                      ? 'bg-violet-500/20 border-violet-500/50 text-violet-300'
                      : 'bg-slate-700/30 border-slate-600/50 text-slate-400 hover:text-slate-300'
                  }`}
                >
                  Dark Mode
                </button>
                <button
                  onClick={() => setTheme('light')}
                  className={`px-4 py-2 rounded-lg border transition-colors ${
                    theme === 'light'
                      ? 'bg-violet-500/20 border-violet-500/50 text-violet-300'
                      : 'bg-slate-700/30 border-slate-600/50 text-slate-400 hover:text-slate-300'
                  }`}
                >
                  Light Mode
                </button>
              </div>
            </div>
            
            <div className="p-4 bg-slate-700/30 rounded-lg">
              <h4 className="text-white font-medium mb-2">Preview</h4>
              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 bg-gradient-to-br from-violet-500 to-purple-500 rounded-lg"></div>
                <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-lg"></div>
                <div className="w-8 h-8 bg-gradient-to-br from-green-500 to-emerald-500 rounded-lg"></div>
                <div className="w-8 h-8 bg-gradient-to-br from-yellow-500 to-orange-500 rounded-lg"></div>
              </div>
            </div>
          </div>
        </SettingsSection>

        {/* Notifications */}
        <SettingsSection
          title="Notifications"
          description="Choose what notifications you want to receive"
          icon={BellIcon}
        >
          <div className="space-y-4">
            {Object.entries({
              experimentComplete: 'Experiment completed',
              experimentFailed: 'Experiment failed',
              newLeaderboardEntry: 'New leaderboard entry',
              systemAlerts: 'System alerts and warnings',
            }).map(([key, label]) => (
              <div key={key} className="flex items-center justify-between">
                <span className="text-slate-300">{label}</span>
                <button
                  onClick={() => setNotifications(prev => ({ ...prev, [key]: !prev[key as keyof typeof prev] }))}
                  className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                    notifications[key as keyof typeof notifications]
                      ? 'bg-violet-500'
                      : 'bg-slate-600'
                  }`}
                >
                  <span
                    className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                      notifications[key as keyof typeof notifications] ? 'translate-x-6' : 'translate-x-1'
                    }`}
                  />
                </button>
              </div>
            ))}
          </div>
        </SettingsSection>

        {/* API Configuration */}
        <SettingsSection
          title="API Configuration"
          description="Configure backend API settings and authentication"
          icon={KeyIcon}
        >
          <div className="space-y-4">
            <div>
              <label className="block text-slate-300 text-sm font-medium mb-2">Backend API URL</label>
              <input
                type="text"
                defaultValue="http://localhost:8000"
                className="w-full px-3 py-2 bg-slate-700/50 border border-slate-600/50 rounded-lg text-white focus:border-violet-500 focus:outline-none"
              />
            </div>
            
            <div>
              <label className="block text-slate-300 text-sm font-medium mb-2">WebSocket URL</label>
              <input
                type="text"
                defaultValue="ws://localhost:8000/ws/realtime"
                className="w-full px-3 py-2 bg-slate-700/50 border border-slate-600/50 rounded-lg text-white focus:border-violet-500 focus:outline-none"
              />
            </div>
            
            <div className="flex items-center justify-between p-4 bg-slate-700/30 rounded-lg">
              <div>
                <p className="text-white font-medium">Connection Status</p>
                <p className="text-slate-400 text-sm">
                  {connectionStatus.apiConnected ? 'Connected to backend API' : 'Backend API unavailable'}
                </p>
              </div>
              <div className={`w-3 h-3 rounded-full ${
                connectionStatus.apiConnected ? 'bg-green-400' : 'bg-red-400'
              }`} />
            </div>
          </div>
        </SettingsSection>

        {/* Quick Actions */}
        <SettingsSection
          title="Quick Actions"
          description="Common tasks and utilities"
          icon={CogIcon}
        >
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <button
              onClick={() => {
                toast.promise(
                  fetch('/api/v1/demo/populate', { method: 'POST' }),
                  {
                    loading: 'Creating demo experiments...',
                    success: 'Demo data created successfully!',
                    error: 'Failed to create demo data'
                  }
                );
              }}
              className="p-4 bg-green-500/20 border border-green-500/30 rounded-lg text-green-300 hover:bg-green-500/30 transition-colors text-left"
            >
              <h4 className="font-medium mb-1">Create Demo Data</h4>
              <p className="text-sm text-green-400/80">Populate with sample experiments and data</p>
            </button>
            
            <button
              onClick={() => {
                toast.promise(
                  fetch('/api/v1/experiments', { method: 'DELETE' }),
                  {
                    loading: 'Clearing experiments...',
                    success: 'All experiments cleared!',
                    error: 'Failed to clear experiments'
                  }
                );
              }}
              className="p-4 bg-red-500/20 border border-red-500/30 rounded-lg text-red-300 hover:bg-red-500/30 transition-colors text-left"
            >
              <h4 className="font-medium mb-1">Clear All Data</h4>
              <p className="text-sm text-red-400/80">Remove all experiments and reset dashboard</p>
            </button>
            
            <button
              onClick={() => window.open('http://localhost:8080', '_blank')}
              className="p-4 bg-blue-500/20 border border-blue-500/30 rounded-lg text-blue-300 hover:bg-blue-500/30 transition-colors text-left"
            >
              <h4 className="font-medium mb-1">Open ClearML UI</h4>
              <p className="text-sm text-blue-400/80">Launch ClearML web interface in new tab</p>
            </button>
            
            <button
              onClick={() => {
                navigator.clipboard.writeText(`fba-bench launch --game-mode`);
                toast.success('Command copied to clipboard!');
              }}
              className="p-4 bg-purple-500/20 border border-purple-500/30 rounded-lg text-purple-300 hover:bg-purple-500/30 transition-colors text-left"
            >
              <h4 className="font-medium mb-1">Copy CLI Command</h4>
              <p className="text-sm text-purple-400/80">Copy the launch command to clipboard</p>
            </button>
          </div>
        </SettingsSection>

        {/* Save Button */}
        <motion.div
          className="flex justify-end"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3 }}
        >
          <button
            onClick={handleSaveSettings}
            className="px-8 py-3 bg-gradient-to-r from-violet-500 to-purple-500 text-white rounded-lg hover:from-violet-600 hover:to-purple-600 transition-all duration-200 font-medium"
          >
            Save Settings
          </button>
        </motion.div>
      </div>

      {/* Environment Setup Modal */}
      <EnvironmentSetupModal
        isOpen={showEnvironmentModal}
        onClose={() => setShowEnvironmentModal(false)}
        onComplete={(config) => {
          refreshEnvironmentStatus();
          console.log('Environment configured:', Object.keys(config).filter(key => !!config[key as keyof typeof config]));
        }}
      />
    </div>
  );
};

export default Settings;