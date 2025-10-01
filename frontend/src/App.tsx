import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Toaster } from 'react-hot-toast';
import { toast } from 'react-hot-toast';
import { KeyIcon, XMarkIcon } from '@heroicons/react/24/outline';

// Components
import Navigation from './components/layout/Navigation';
import Dashboard from './pages/Dashboard';
import Experiments from './pages/Experiments';
import Templates from './pages/Templates';
import Leaderboard from './pages/Leaderboard';
import Settings from './pages/Settings';
import MedusaDashboard from './pages/medusa/MedusaDashboard';  // Import the new MedusaDashboard
import MedusaLogs from './pages/MedusaLogs';
import LoadingScreen from './components/common/LoadingScreen';
import ConfigurationWizard from './components/setup/ConfigurationWizard';
import GuidedTour from './components/tour/GuidedTour';
import { tourSteps } from './config/tour-steps';

// Services
import { apiService } from './services/api';
import { useAppStore } from './store/appStore';
import { environmentService } from './services/environment';
import EnvironmentSetupModal from './components/setup/EnvironmentSetupModal';

// Types
interface AppStatus {
  apiConnected: boolean;
  clearmlConnected: boolean;
  loading: boolean;
  configValid: boolean;
  configChecked: boolean;
  tourCompleted: boolean;
  environmentSetup: boolean;
  showEnvironmentPrompt: boolean;
}

interface ConfigurationData {
  environment: string;
  authEnabled: boolean;
  corsOrigins: string;
  mongoUsername: string;
  mongoPassword: string;
  redisPassword: string;
  clearmlAccessKey?: string;
  clearmlSecretKey?: string;
}

class ErrorBoundary extends React.Component<{ children: React.ReactNode }, { hasError: boolean }> {
  constructor(props: { children: React.ReactNode }) {
    super(props);
    this.state = { hasError: false };
  }
  static getDerivedStateFromError() {
    return { hasError: true };
  }
  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('ErrorBoundary caught an error', error, errorInfo);
  }
  render() {
    if (this.state.hasError) {
      return <div role="alert" className="p-4 text-red-700 bg-red-50 border border-red-200 rounded">Something went wrong.</div>;
    }
    return this.props.children;
  }
}

function App() {
  const [status, setStatus] = useState<AppStatus>({
    apiConnected: false,
    clearmlConnected: false,
    loading: true,
    configValid: false,
    configChecked: false,
    tourCompleted: false,
    environmentSetup: false,
    showEnvironmentPrompt: false
  });

  const [showEnvironmentModal, setShowEnvironmentModal] = useState(false);

  const { setConnectionStatus } = useAppStore();

  useEffect(() => {
    initializeApp();
  }, []);

  const initializeApp = async () => {
    try {
      // Check for persistent skip flag first
      const skipWizard = localStorage.getItem('fba_skip_config_wizard') === 'true';
      
      // First check configuration status
      const configResponse = await apiService.checkEnvConfiguration();
      let configValid = configResponse.data.valid;
      
      if (skipWizard) {
        configValid = true; // Force bypass if user skipped before
        toast('Using previously skipped configuration. Update in Settings if needed.', {
          duration: 5000,
          icon: 'ℹ️',
          style: { background: '#10b981', color: 'white' }
        });
      }
      
      // Check environment setup (API keys)
      const environmentSetup = environmentService.isBasicSetupComplete();
      const missingKeys = environmentService.getMissingCriticalKeys();
      
      setStatus(prev => ({
        ...prev,
        configValid,
        configChecked: true,
        environmentSetup,
        showEnvironmentPrompt: !environmentSetup && missingKeys.length > 0,
        loading: false
      }));

      if (!configValid && !skipWizard) {
        return; // Show configuration wizard
      }

      // Show environment prompt if basic setup is incomplete
      if (!environmentSetup && missingKeys.length > 0) {
        // Delay the prompt slightly to let the user see the dashboard first
        setTimeout(() => {
          if (missingKeys.length > 0) {
            toast.error(
              `Missing API configuration: ${missingKeys.join(', ')}. Configure in Settings.`,
              { duration: 6000 }
            );
          }
        }, 2000);
      }

      // Check API connection
      const healthCheck = await apiService.checkHealth();
      const apiConnected = healthCheck.data.status === 'healthy';
      
      // Check ClearML connection
      let clearmlConnected = false;
      try {
        const clearmlStatus = await apiService.getClearMLStatus();
        clearmlConnected = clearmlStatus.data.connected;
      } catch (error) {
        console.warn('ClearML not available:', error);
      }

      setStatus(prev => ({
        ...prev,
        apiConnected,
        clearmlConnected
      }));

      setConnectionStatus({ apiConnected, clearmlConnected });

    } catch (error) {
      console.error('Failed to initialize app:', error);
      setStatus(prev => ({
        ...prev,
        configValid: false,
        configChecked: true,
        loading: false
      }));
    }
  };

  const handleConfigComplete = async (config: ConfigurationData) => {
    try {
      // Convert ConfigurationData to ConfigUpdateRequest format
      const updateRequest = {
        environment: config.environment,
        auth_enabled: config.authEnabled,
        cors_origins: config.corsOrigins,
        mongo_username: config.mongoUsername,
        mongo_password: config.mongoPassword,
        redis_password: config.redisPassword,
        clearml_access_key: config.clearmlAccessKey,
        clearml_secret_key: config.clearmlSecretKey,
      };
      
      const response = await apiService.updateConfiguration(updateRequest);
      if (response.data.success) {
        toast.success('Configuration saved successfully! Restarting application...');
        setTimeout(() => {
          window.location.reload();
        }, 2000);
      }
    } catch (error) {
      toast.error('Failed to save configuration. Please try again.');
    }
  };

  const handleWizardSkip = () => {
    localStorage.setItem('fba_skip_config_wizard', 'true');
    setStatus(prev => ({ ...prev, configValid: true }));
    toast.success('Configuration skipped. You can update settings later in the Settings page.');
  };

  const handleTourComplete = () => {
    setStatus(prev => ({ ...prev, tourCompleted: true }));
    // Save tour completion to localStorage
    localStorage.setItem('fba_bench_tour_completed', 'true');
  };

  const handleEnvironmentComplete = () => {
    setShowEnvironmentModal(false);
    setStatus(prev => ({ ...prev, environmentSetup: true, showEnvironmentPrompt: false }));
    // Refresh the app to pick up new credentials
    setTimeout(() => {
      initializeApp();
    }, 500);
  };

  const showTour = !status.tourCompleted && status.configChecked && status.configValid && status.environmentSetup;

  if (status.loading) {
    return <LoadingScreen />;
  }

  if (!status.configChecked || (!status.configValid && localStorage.getItem('fba_skip_config_wizard') !== 'true')) {
    return (
      <ConfigurationWizard
        onComplete={handleConfigComplete}
        onSkip={handleWizardSkip}
      />
    );
  }

  return (
    <ErrorBoundary>
      <Router>
        <div className="min-h-screen bg-white">
          <Toaster
            position="top-right"
            toastOptions={{
              duration: 4000,
              style: {
                background: 'white',
                color: '#374151',
                border: '1px solid #d1d5db',
                boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1)',
              },
            }}
          />
          
          <Navigation
            apiConnected={status.apiConnected}
            clearmlConnected={status.clearmlConnected}
          />
          
          <motion.main
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="pt-16"
          >
            <Routes>
              <Route path="/" element={<Navigate to="/dashboard" replace />} />
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/experiments" element={<Experiments />} />
              <Route path="/templates" element={<Templates />} />
              <Route path="/leaderboard" element={<Leaderboard />} />
              <Route path="/medusa" element={<MedusaDashboard />} />  {/* Updated route to /medusa using MedusaDashboard */}
              <Route path="/settings" element={<Settings />} />
              <Route path="/medusa-logs" element={<MedusaLogs />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </motion.main>

          {showTour && (
            <GuidedTour
              isOpen={showTour}
              onClose={handleTourComplete}
              steps={[
                {
                  id: 0,
                  title: 'Welcome to FBA-Bench',
                  description: 'This guided tour will help you get started with the platform.',
                  target: '.logo-brand',
                  position: 'bottom',
                  content: (
                    <div>
                      <p>You&apos;re now using the FBA-Bench platform for business agent simulation.</p>
                      <p className="mt-2">Let&apos;s explore the main features.</p>
                    </div>
                  )
                },
                {
                  id: 1,
                  title: 'Dashboard Overview',
                  description: 'The dashboard shows key metrics and recent activity.',
                  target: '.metric-card',
                  position: 'right',
                  content: (
                    <div>
                      <p>Monitor your experiments with real-time metrics and performance indicators.</p>
                      <p className="mt-2 text-sm text-gray-600">Click &quot;Start New Experiment&quot; to begin your first simulation.</p>
                    </div>
                  )
                },
                {
                  id: 2,
                  title: 'Experiments Management',
                  description: 'Manage all your business simulations from the Experiments page.',
                  target: '.nav-experiments',
                  position: 'bottom',
                  content: (
                    <div>
                      <p>Create, monitor, and analyze your agent experiments.</p>
                      <p className="mt-2 text-sm text-gray-600">Track performance, view results, and compare different strategies.</p>
                    </div>
                  )
                },
                {
                  id: 3,
                  title: 'Leaderboard',
                  description: 'See how your agents perform compared to others.',
                  target: '.nav-leaderboard',
                  position: 'bottom',
                  content: (
                    <div>
                      <p>View the top performing agents and benchmark your results.</p>
                      <p className="mt-2 text-sm text-gray-600">Use this to identify the best strategies and areas for improvement.</p>
                    </div>
                  )
                },
                {
                  id: 4,
                  title: 'Settings & Configuration',
                  description: 'Customize your platform settings and integrations.',
                  target: '.nav-settings',
                  position: 'bottom',
                  content: (
                    <div>
                      <p>Configure ClearML integration, API settings, and user preferences.</p>
                      <p className="mt-2 text-sm text-gray-600">You can always return to this tour from the help menu.</p>
                    </div>
                  )
                }
              ]}
            />
          )}

          {/* Environment Setup Modal */}
          <EnvironmentSetupModal
            isOpen={showEnvironmentModal}
            onClose={() => setShowEnvironmentModal(false)}
            onComplete={handleEnvironmentComplete}
          />

          {/* Environment Setup Banner */}
          {status.showEnvironmentPrompt && status.configValid && (
            <motion.div
              initial={{ opacity: 0, y: -50 }}
              animate={{ opacity: 1, y: 0 }}
              className="fixed top-16 left-0 right-0 z-40 mx-4 mt-4"
            >
              <div className="bg-gradient-to-r from-amber-500/90 to-orange-500/90 backdrop-blur-sm border border-amber-400/50 rounded-lg p-4 shadow-lg">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className="p-2 bg-white/20 rounded-lg">
                      <KeyIcon className="h-5 w-5 text-white" />
                    </div>
                    <div>
                      <h3 className="text-white font-semibold">Environment Setup Needed</h3>
                      <p className="text-amber-100 text-sm">
                        Configure API keys to enable full functionality. Missing: {environmentService.getMissingCriticalKeys().join(', ')}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => setShowEnvironmentModal(true)}
                      className="px-4 py-2 bg-white/20 text-white rounded-lg hover:bg-white/30 transition-colors border border-white/30"
                    >
                      Configure Now
                    </button>
                    <button
                      onClick={() => setStatus(prev => ({ ...prev, showEnvironmentPrompt: false }))}
                      className="p-2 text-white/80 hover:text-white transition-colors"
                    >
                      <XMarkIcon className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              </div>
            </motion.div>
          )}
        </div>
      </Router>
    </ErrorBoundary>
  );
}

export default App;
