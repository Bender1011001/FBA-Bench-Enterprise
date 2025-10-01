import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  CogIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  DocumentTextIcon,
  ServerIcon,
  ShieldCheckIcon,
  ArrowRightIcon,
  ArrowLeftIcon
} from '@heroicons/react/24/outline';

interface ConfigurationStep {
  id: string;
  title: string;
  description: string;
  icon: React.ElementType;
  required: boolean;
}

interface ConfigurationData {
  environment: 'development' | 'staging' | 'production';
  authEnabled: boolean;
  corsOrigins: string;
  mongoUsername: string;
  mongoPassword: string;
  redisPassword: string;
  clearmlAccessKey?: string;
  clearmlSecretKey?: string;
}

interface ConfigurationWizardProps {
  onComplete: (config: ConfigurationData) => void;
  onSkip: () => void;
  initialConfig?: Partial<ConfigurationData>;
}

const ConfigurationWizard: React.FC<ConfigurationWizardProps> = ({
  onComplete,
  onSkip,
  initialConfig = {}
}) => {
  const [currentStep, setCurrentStep] = useState(0);
  const [config, setConfig] = useState<ConfigurationData>({
    environment: 'development',
    authEnabled: false,
    corsOrigins: 'http://localhost:5173,http://localhost:3000',
    mongoUsername: 'clearml',
    mongoPassword: '',
    redisPassword: '',
    clearmlAccessKey: '',
    clearmlSecretKey: '',
    ...initialConfig
  });

  const steps: ConfigurationStep[] = [
    {
      id: 'environment',
      title: 'Environment Setup',
      description: 'Configure your deployment environment and security settings',
      icon: CogIcon,
      required: true
    },
    {
      id: 'database',
      title: 'Database Configuration',
      description: 'Set up MongoDB and Redis credentials for data storage',
      icon: ServerIcon,
      required: true
    },
    {
      id: 'clearml',
      title: 'ClearML Integration',
      description: 'Optional: Connect to ClearML for experiment tracking',
      icon: DocumentTextIcon,
      required: false
    },
    {
      id: 'review',
      title: 'Review & Confirm',
      description: 'Review your configuration before saving',
      icon: ShieldCheckIcon,
      required: true
    }
  ];

  useEffect(() => {
    // Generate secure passwords if not provided
    if (!config.mongoPassword) {
      setConfig(prev => ({
        ...prev,
        mongoPassword: generateSecurePassword(),
        redisPassword: generateSecurePassword()
      }));
    }
  }, []);

  const generateSecurePassword = (): string => {
    const charset = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*';
    let password = '';
    for (let i = 0; i < 16; i++) {
      password += charset.charAt(Math.floor(Math.random() * charset.length));
    }
    return password;
  };

  const updateConfig = (updates: Partial<ConfigurationData>) => {
    setConfig(prev => ({ ...prev, ...updates }));
  };

  const validateCurrentStep = (): boolean => {
    const step = steps[currentStep];
    
    switch (step.id) {
      case 'environment':
        return config.environment && config.corsOrigins.length > 0;
      case 'database':
        return config.mongoUsername.length > 0 && 
               config.mongoPassword.length >= 8 && 
               config.redisPassword.length >= 8;
      case 'clearml':
        return true; // Optional step
      case 'review':
        return true;
      default:
        return false;
    }
  };

  const nextStep = () => {
    if (currentStep < steps.length - 1) {
      setCurrentStep(prev => prev + 1);
    }
  };

  const prevStep = () => {
    if (currentStep > 0) {
      setCurrentStep(prev => prev - 1);
    }
  };

  const handleComplete = () => {
    onComplete(config);
  };

  const renderStepContent = () => {
    const step = steps[currentStep];
    
    switch (step.id) {
      case 'environment':
        return (
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Environment Type
              </label>
              <select
                value={config.environment}
                onChange={(e) => updateConfig({ environment: e.target.value as 'development' | 'staging' | 'production' })}
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="development">Development (Recommended for testing)</option>
                <option value="staging">Staging (Pre-production)</option>
                <option value="production">Production (Live deployment)</option>
              </select>
              <p className="text-sm text-gray-500 mt-1">
                Development mode disables authentication and enables debugging features
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Enable Authentication
              </label>
              <div className="flex items-center space-x-3">
                <input
                  type="checkbox"
                  checked={config.authEnabled}
                  onChange={(e) => updateConfig({ authEnabled: e.target.checked })}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <span className="text-sm text-gray-700">
                  Enable JWT authentication for API access
                </span>
              </div>
              <p className="text-sm text-gray-500 mt-1">
                Recommended for production environments
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Allowed Origins (CORS)
              </label>
              <input
                type="text"
                value={config.corsOrigins}
                onChange={(e) => updateConfig({ corsOrigins: e.target.value })}
                placeholder="http://localhost:5173,http://localhost:3000"
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
              <p className="text-sm text-gray-500 mt-1">
                Comma-separated list of allowed frontend URLs
              </p>
            </div>
          </div>
        );

      case 'database':
        return (
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                MongoDB Username
              </label>
              <input
                type="text"
                value={config.mongoUsername}
                onChange={(e) => updateConfig({ mongoUsername: e.target.value })}
                placeholder="clearml"
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                MongoDB Password
              </label>
              <input
                type="password"
                value={config.mongoPassword}
                onChange={(e) => updateConfig({ mongoPassword: e.target.value })}
                placeholder="Secure password (min 8 characters)"
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
              <button
                type="button"
                onClick={() => updateConfig({ mongoPassword: generateSecurePassword() })}
                className="mt-2 text-sm text-blue-600 hover:text-blue-800"
              >
                Generate secure password
              </button>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Redis Password
              </label>
              <input
                type="password"
                value={config.redisPassword}
                onChange={(e) => updateConfig({ redisPassword: e.target.value })}
                placeholder="Secure password (min 8 characters)"
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
              <button
                type="button"
                onClick={() => updateConfig({ redisPassword: generateSecurePassword() })}
                className="mt-2 text-sm text-blue-600 hover:text-blue-800"
              >
                Generate secure password
              </button>
            </div>
          </div>
        );

      case 'clearml':
        return (
          <div className="space-y-6">
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <div className="flex items-start space-x-3">
                <DocumentTextIcon className="h-5 w-5 text-blue-500 mt-0.5" />
                <div>
                  <h4 className="text-sm font-medium text-blue-800">Optional: ClearML Integration</h4>
                  <p className="text-sm text-blue-700 mt-1">
                    ClearML provides experiment tracking, model management, and visualization. 
                    You can skip this step and configure it later in Settings.
                  </p>
                </div>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                ClearML Access Key
              </label>
              <input
                type="text"
                value={config.clearmlAccessKey || ''}
                onChange={(e) => updateConfig({ clearmlAccessKey: e.target.value })}
                placeholder="Your ClearML access key (optional)"
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                ClearML Secret Key
              </label>
              <input
                type="password"
                value={config.clearmlSecretKey || ''}
                onChange={(e) => updateConfig({ clearmlSecretKey: e.target.value })}
                placeholder="Your ClearML secret key (optional)"
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>

            <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
              <h4 className="text-sm font-medium text-gray-800 mb-2">How to get ClearML keys:</h4>
              <ol className="text-sm text-gray-700 space-y-1 list-decimal list-inside">
                <li>Sign up at <a href="https://clear.ml" target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">clear.ml</a></li>
                <li>Go to Settings → Workspace → Create new credentials</li>
                <li>Copy the Access Key and Secret Key</li>
              </ol>
            </div>
          </div>
        );

      case 'review':
        return (
          <div className="space-y-6">
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-6">
              <h4 className="text-lg font-medium text-gray-900 mb-4">Configuration Summary</h4>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <h5 className="text-sm font-medium text-gray-700 mb-2">Environment</h5>
                  <p className="text-sm text-gray-600 capitalize">{config.environment}</p>
                </div>
                
                <div>
                  <h5 className="text-sm font-medium text-gray-700 mb-2">Authentication</h5>
                  <p className="text-sm text-gray-600">{config.authEnabled ? 'Enabled' : 'Disabled'}</p>
                </div>
                
                <div>
                  <h5 className="text-sm font-medium text-gray-700 mb-2">Database</h5>
                  <p className="text-sm text-gray-600">
                    MongoDB: {config.mongoUsername}<br/>
                    Redis: Configured
                  </p>
                </div>
                
                <div>
                  <h5 className="text-sm font-medium text-gray-700 mb-2">ClearML</h5>
                  <p className="text-sm text-gray-600">
                    {config.clearmlAccessKey ? 'Configured' : 'Not configured (optional)'}
                  </p>
                </div>
              </div>
            </div>

            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
              <div className="flex items-start space-x-3">
                <ExclamationTriangleIcon className="h-5 w-5 text-yellow-500 mt-0.5" />
                <div>
                  <h4 className="text-sm font-medium text-yellow-800">Important</h4>
                  <p className="text-sm text-yellow-700 mt-1">
                    This configuration will be saved to your .env file. Keep your passwords secure
                    and does not share them with others.
                  </p>
                </div>
              </div>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="bg-white rounded-xl shadow-2xl max-w-2xl w-full max-h-[90vh] flex flex-col"
      >
        {/* Header */}
        <div className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white p-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <CogIcon className="h-8 w-8" />
              <div>
                <h2 className="text-2xl font-bold">FBA-Bench Configuration</h2>
                <p className="text-blue-100">Set up your business simulation platform</p>
              </div>
            </div>
            <button
              onClick={onSkip}
              className="px-4 py-2 bg-yellow-400 text-yellow-900 rounded-lg hover:bg-yellow-300 transition-colors font-semibold border-2 border-yellow-300 shadow-lg"
            >
              ⚡ Skip Setup
            </button>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="bg-gray-50 px-6 py-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-700">
              Step {currentStep + 1} of {steps.length}
            </span>
            <span className="text-sm text-gray-500">
              {Math.round(((currentStep + 1) / steps.length) * 100)}% Complete
            </span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <motion.div
              className="bg-blue-600 h-2 rounded-full"
              initial={{ width: 0 }}
              animate={{ width: `${((currentStep + 1) / steps.length) * 100}%` }}
              transition={{ duration: 0.3 }}
            />
          </div>
        </div>

        {/* Step Navigation */}
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="flex space-x-4">
            {steps.map((step, index) => {
              const StepIcon = step.icon;
              const isActive = index === currentStep;
              const isCompleted = index < currentStep;
              
              return (
                <div
                  key={step.id}
                  className={`flex items-center space-x-2 px-3 py-2 rounded-lg transition-colors ${
                    isActive
                      ? 'bg-blue-100 text-blue-700'
                      : isCompleted
                      ? 'bg-green-100 text-green-700'
                      : 'text-gray-500'
                  }`}
                >
                  {isCompleted ? (
                    <CheckCircleIcon className="h-5 w-5" />
                  ) : (
                    <StepIcon className="h-5 w-5" />
                  )}
                  <span className="text-sm font-medium hidden sm:block">{step.title}</span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Step Content */}
        <div className="flex-1 p-6 overflow-y-auto">
          <motion.div
            key={currentStep}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.3 }}
          >
            <h3 className="text-xl font-semibold text-gray-900 mb-2">
              {steps[currentStep].title}
            </h3>
            <p className="text-gray-600 mb-6">
              {steps[currentStep].description}
            </p>
            
            {renderStepContent()}
          </motion.div>
        </div>

        {/* Footer */}
        <div className="bg-gray-50 px-6 py-4 flex items-center justify-between">
          <div className="flex space-x-3">
            <button
              onClick={onSkip}
              className="px-6 py-2 bg-yellow-100 text-yellow-800 border border-yellow-300 rounded-lg hover:bg-yellow-200 transition-colors font-medium"
            >
              ⚡ Skip Setup - Use Defaults
            </button>
          </div>
          
          <div className="flex space-x-3">
            {currentStep > 0 && (
              <button
                onClick={prevStep}
                className="flex items-center space-x-2 px-4 py-2 text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
              >
                <ArrowLeftIcon className="h-4 w-4" />
                <span>Previous</span>
              </button>
            )}
            
            {currentStep < steps.length - 1 ? (
              <button
                onClick={nextStep}
                disabled={currentStep === 0 ? false : !validateCurrentStep()}
                className="flex items-center space-x-2 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                <span>Next</span>
                <ArrowRightIcon className="h-4 w-4" />
              </button>
            ) : (
              <button
                onClick={handleComplete}
                disabled={!validateCurrentStep()}
                className="flex items-center space-x-2 px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                <CheckCircleIcon className="h-4 w-4" />
                <span>Complete Setup</span>
              </button>
            )}
          </div>
        </div>
      </motion.div>
    </div>
  );
};

export default ConfigurationWizard;