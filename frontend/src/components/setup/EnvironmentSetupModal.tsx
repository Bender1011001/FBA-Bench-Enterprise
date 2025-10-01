import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  XMarkIcon,
  KeyIcon,
  CheckCircleIcon,
  XCircleIcon,
  EyeIcon,
  EyeSlashIcon,
  InformationCircleIcon,
  CloudIcon,
  CpuChipIcon,
  ShieldCheckIcon,
  ExclamationTriangleIcon,
  ArrowPathIcon
} from '@heroicons/react/24/outline';
import { toast } from 'react-hot-toast';
import { environmentService, type EnvironmentConfig, type ServiceStatus, type ConnectionTestResult } from '../../services/environment';

interface EnvironmentSetupModalProps {
  isOpen: boolean;
  onClose: () => void;
  onComplete?: (config: EnvironmentConfig) => void;
}

interface FormData {
  openaiApiKey: string;
  openrouterApiKey: string;
  clearmlAccessKey: string;
  clearmlSecretKey: string;
  saveToStorage: boolean;
}

interface TestStatus {
  service: string;
  testing: boolean;
  result?: 'success' | 'failed';
  message?: string;
}

const EnvironmentSetupModal: React.FC<EnvironmentSetupModalProps> = ({ 
  isOpen, 
  onClose, 
  onComplete 
}) => {
  const [formData, setFormData] = useState<FormData>({
    openaiApiKey: '',
    openrouterApiKey: '',
    clearmlAccessKey: '',
    clearmlSecretKey: '',
    saveToStorage: true,
  });

  const [showKeys, setShowKeys] = useState({
    openai: false,
    openrouter: false,
    clearmlAccess: false,
    clearmlSecret: false,
  });

  const [testStatuses, setTestStatuses] = useState<TestStatus[]>([
    { service: 'openai', testing: false },
    { service: 'openrouter', testing: false },
    { service: 'clearml', testing: false },
  ]);

  const [serviceStatuses, setServiceStatuses] = useState<ServiceStatus[]>([]);

  // Load existing configuration when modal opens
  useEffect(() => {
    if (isOpen) {
      const existing = environmentService.getStoredApiKeys();
      const statuses = environmentService.getServiceStatuses();
      
      setFormData({
        openaiApiKey: existing.openaiApiKey || '',
        openrouterApiKey: existing.openrouterApiKey || '',
        clearmlAccessKey: existing.clearmlAccessKey || '',
        clearmlSecretKey: existing.clearmlSecretKey || '',
        saveToStorage: true,
      });
      
      setServiceStatuses(statuses);
    }
  }, [isOpen]);

  const updateTestStatus = (service: string, update: Partial<TestStatus>) => {
    setTestStatuses(prev => prev.map(status => 
      status.service === service ? { ...status, ...update } : status
    ));
  };

  const testOpenAIConnection = async (apiKey: string): Promise<ConnectionTestResult> => {
    try {
      const response = await fetch('https://api.openai.com/v1/models', {
        headers: {
          'Authorization': `Bearer ${apiKey}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        return { success: true, message: 'OpenAI API connection successful' };
      } else if (response.status === 401) {
        return { success: false, message: 'Invalid API key' };
      } else {
        return { success: false, message: `API error: ${response.status}` };
      }
    } catch (error) {
      return { 
        success: false, 
        message: 'Connection failed',
        details: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  };

  const testOpenRouterConnection = async (apiKey: string): Promise<ConnectionTestResult> => {
    try {
      const response = await fetch('https://openrouter.ai/api/v1/models', {
        headers: {
          'Authorization': `Bearer ${apiKey}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        return { success: true, message: 'OpenRouter API connection successful' };
      } else if (response.status === 401) {
        return { success: false, message: 'Invalid API key' };
      } else {
        return { success: false, message: `API error: ${response.status}` };
      }
    } catch (error) {
      return { 
        success: false, 
        message: 'Connection failed',
        details: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  };

  const testClearMLConnection = async (accessKey: string, secretKey: string): Promise<ConnectionTestResult> => {
    try {
      // For local ClearML, we'll try to connect to the API server
      const apiHost = 'http://localhost:8008';
      
      // Try basic auth first
      const credentials = btoa(`${accessKey}:${secretKey}`);
      const response = await fetch(`${apiHost}/auth.login`, {
        method: 'POST',
        headers: {
          'Authorization': `Basic ${credentials}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          access_key: accessKey,
          secret_key: secretKey,
        }),
      });

      if (response.ok) {
        return { success: true, message: 'ClearML connection successful' };
      } else if (response.status === 401) {
        return { success: false, message: 'Invalid credentials' };
      } else {
        return { success: false, message: `ClearML API error: ${response.status}` };
      }
    } catch (error) {
      // If the API server isn't running, that's also useful information
      return { 
        success: false, 
        message: 'ClearML server not reachable',
        details: 'Make sure ClearML server is running on localhost:8008'
      };
    }
  };

  const handleTestConnection = async (service: string) => {
    updateTestStatus(service, { testing: true, result: undefined, message: undefined });
    
    let result: ConnectionTestResult;
    
    try {
      switch (service) {
        case 'openai':
          if (!formData.openaiApiKey.trim()) {
            result = { success: false, message: 'Please enter an OpenAI API key first' };
            break;
          }
          result = await testOpenAIConnection(formData.openaiApiKey);
          break;
          
        case 'openrouter':
          if (!formData.openrouterApiKey.trim()) {
            result = { success: false, message: 'Please enter an OpenRouter API key first' };
            break;
          }
          result = await testOpenRouterConnection(formData.openrouterApiKey);
          break;
          
        case 'clearml':
          if (!formData.clearmlAccessKey.trim() || !formData.clearmlSecretKey.trim()) {
            result = { success: false, message: 'Please enter both ClearML access and secret keys' };
            break;
          }
          result = await testClearMLConnection(formData.clearmlAccessKey, formData.clearmlSecretKey);
          break;
          
        default:
          result = { success: false, message: 'Unknown service' };
      }

      // Update service status in environment service
      environmentService.setTestResult(service, result.success ? 'success' : 'failed');
      
      updateTestStatus(service, { 
        testing: false, 
        result: result.success ? 'success' : 'failed',
        message: result.message
      });

      if (result.success) {
        toast.success(result.message);
      } else {
        toast.error(result.message);
      }
      
    } catch (error) {
      updateTestStatus(service, { 
        testing: false, 
        result: 'failed',
        message: 'Test failed unexpectedly'
      });
      toast.error('Connection test failed');
    }
  };

  const handleSave = () => {
    try {
      // Validate keys before saving
      const errors: string[] = [];
      
      if (formData.openaiApiKey.trim()) {
        const validation = environmentService.validateApiKey('openai', formData.openaiApiKey);
        if (!validation.valid) {
          errors.push(`OpenAI: ${validation.message}`);
        }
      }
      
      if (formData.openrouterApiKey.trim()) {
        const validation = environmentService.validateApiKey('openrouter', formData.openrouterApiKey);
        if (!validation.valid) {
          errors.push(`OpenRouter: ${validation.message}`);
        }
      }
      
      if (formData.clearmlAccessKey.trim()) {
        const validation = environmentService.validateApiKey('clearml', formData.clearmlAccessKey);
        if (!validation.valid) {
          errors.push(`ClearML Access Key: ${validation.message}`);
        }
      }
      
      if (formData.clearmlSecretKey.trim()) {
        const validation = environmentService.validateApiKey('clearml', formData.clearmlSecretKey);
        if (!validation.valid) {
          errors.push(`ClearML Secret Key: ${validation.message}`);
        }
      }

      if (errors.length > 0) {
        toast.error(`Validation errors: ${errors.join(', ')}`);
        return;
      }

      // Save keys to storage if enabled
      if (formData.saveToStorage) {
        if (formData.openaiApiKey.trim()) {
          environmentService.setApiKey('OPENAI_API_KEY', formData.openaiApiKey);
        }
        if (formData.openrouterApiKey.trim()) {
          environmentService.setApiKey('OPENROUTER_API_KEY', formData.openrouterApiKey);
        }
        if (formData.clearmlAccessKey.trim()) {
          environmentService.setApiKey('CLEARML_ACCESS_KEY', formData.clearmlAccessKey);
        }
        if (formData.clearmlSecretKey.trim()) {
          environmentService.setApiKey('CLEARML_SECRET_KEY', formData.clearmlSecretKey);
        }
      }

      // Call completion callback
      onComplete?.(environmentService.getStoredApiKeys());
      
      toast.success('Environment configuration saved successfully!');
      onClose();
      
    } catch (error) {
      console.error('Save error:', error);
      toast.error('Failed to save configuration');
    }
  };

  const handleClearAll = () => {
    environmentService.clearApiKeys();
    setFormData({
      openaiApiKey: '',
      openrouterApiKey: '',
      clearmlAccessKey: '',
      clearmlSecretKey: '',
      saveToStorage: true,
    });
    setTestStatuses(prev => prev.map(status => ({ 
      ...status, 
      testing: false, 
      result: undefined, 
      message: undefined 
    })));
    toast.success('All API keys cleared');
  };

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
        onClick={onClose}
      >
        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 20 }}
          onClick={(e) => e.stopPropagation()}
          className="bg-slate-800 rounded-xl border border-slate-700 shadow-2xl max-w-3xl w-full max-h-[90vh] overflow-y-auto"
        >
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b border-slate-700">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-violet-500/20 rounded-lg border border-violet-500/30">
                <KeyIcon className="h-6 w-6 text-violet-400" />
              </div>
              <div>
                <h2 className="text-xl font-semibold text-white">Environment Setup</h2>
                <p className="text-slate-400 text-sm">Configure API keys and credentials for FBA-Bench</p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="p-2 text-slate-400 hover:text-white hover:bg-slate-700 rounded-lg transition-colors"
            >
              <XMarkIcon className="h-5 w-5" />
            </button>
          </div>

          {/* Content */}
          <div className="p-6 space-y-6">
            {/* Security Notice */}
            <div className="flex items-start space-x-3 p-4 bg-amber-500/10 border border-amber-500/20 rounded-lg">
              <ExclamationTriangleIcon className="h-5 w-5 text-amber-400 flex-shrink-0 mt-0.5" />
              <div className="text-sm">
                <p className="text-amber-300 font-medium mb-1">Security Notice</p>
                <p className="text-amber-200/80">
                  API keys are stored in browser localStorage. For enhanced security in production environments, 
                  consider using environment variables or secure credential management systems.
                </p>
              </div>
            </div>

            {/* OpenAI Configuration */}
            <div className="space-y-4">
              <div className="flex items-center space-x-3">
                <div className="p-2 bg-green-500/20 rounded-lg border border-green-500/30">
                  <CloudIcon className="h-5 w-5 text-green-400" />
                </div>
                <div>
                  <h3 className="text-lg font-medium text-white">OpenAI API</h3>
                  <p className="text-slate-400 text-sm">Optional - For GPT models and OpenAI-powered agents</p>
                </div>
              </div>

              <div className="space-y-3">
                <div>
                  <label className="block text-slate-300 text-sm font-medium mb-2">
                    OpenAI API Key
                  </label>
                  <div className="relative">
                    <input
                      type={showKeys.openai ? 'text' : 'password'}
                      value={formData.openaiApiKey}
                      onChange={(e) => setFormData(prev => ({ ...prev, openaiApiKey: e.target.value }))}
                      placeholder="sk-..."
                      className="w-full px-3 py-2 pr-20 bg-slate-700/50 border border-slate-600/50 rounded-lg text-white placeholder-slate-400 focus:border-violet-500 focus:outline-none"
                    />
                    <div className="absolute right-2 top-1/2 transform -translate-y-1/2 flex items-center space-x-1">
                      <button
                        type="button"
                        onClick={() => setShowKeys(prev => ({ ...prev, openai: !prev.openai }))}
                        className="p-1 text-slate-400 hover:text-white transition-colors"
                      >
                        {showKeys.openai ? (
                          <EyeSlashIcon className="h-4 w-4" />
                        ) : (
                          <EyeIcon className="h-4 w-4" />
                        )}
                      </button>
                      <button
                        type="button"
                        onClick={() => handleTestConnection('openai')}
                        disabled={!formData.openaiApiKey.trim() || testStatuses.find(s => s.service === 'openai')?.testing}
                        className="p-1 text-slate-400 hover:text-white disabled:opacity-50 transition-colors"
                      >
                        {testStatuses.find(s => s.service === 'openai')?.testing ? (
                          <ArrowPathIcon className="h-4 w-4 animate-spin" />
                        ) : testStatuses.find(s => s.service === 'openai')?.result === 'success' ? (
                          <CheckCircleIcon className="h-4 w-4 text-green-400" />
                        ) : testStatuses.find(s => s.service === 'openai')?.result === 'failed' ? (
                          <XCircleIcon className="h-4 w-4 text-red-400" />
                        ) : (
                          <InformationCircleIcon className="h-4 w-4" />
                        )}
                      </button>
                    </div>
                  </div>
                  <div className="flex items-center justify-between mt-1">
                    <p className="text-slate-400 text-xs">
                      Get your key from{' '}
                      <a 
                        href="https://platform.openai.com/api-keys" 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="text-violet-400 hover:text-violet-300 underline"
                      >
                        OpenAI Platform
                      </a>
                    </p>
                    {testStatuses.find(s => s.service === 'openai')?.message && (
                      <p className={`text-xs ${
                        testStatuses.find(s => s.service === 'openai')?.result === 'success' ? 'text-green-400' : 'text-red-400'
                      }`}>
                        {testStatuses.find(s => s.service === 'openai')?.message}
                      </p>
                    )}
                  </div>
                </div>
              </div>
            </div>

            {/* OpenRouter Configuration */}
            <div className="space-y-4">
              <div className="flex items-center space-x-3">
                <div className="p-2 bg-blue-500/20 rounded-lg border border-blue-500/30">
                  <CloudIcon className="h-5 w-5 text-blue-400" />
                </div>
                <div>
                  <h3 className="text-lg font-medium text-white">OpenRouter API</h3>
                  <p className="text-slate-400 text-sm">Optional - For accessing multiple LLM providers through one API</p>
                </div>
              </div>

              <div className="space-y-3">
                <div>
                  <label className="block text-slate-300 text-sm font-medium mb-2">
                    OpenRouter API Key
                  </label>
                  <div className="relative">
                    <input
                      type={showKeys.openrouter ? 'text' : 'password'}
                      value={formData.openrouterApiKey}
                      onChange={(e) => setFormData(prev => ({ ...prev, openrouterApiKey: e.target.value }))}
                      placeholder="sk-or-..."
                      className="w-full px-3 py-2 pr-20 bg-slate-700/50 border border-slate-600/50 rounded-lg text-white placeholder-slate-400 focus:border-violet-500 focus:outline-none"
                    />
                    <div className="absolute right-2 top-1/2 transform -translate-y-1/2 flex items-center space-x-1">
                      <button
                        type="button"
                        onClick={() => setShowKeys(prev => ({ ...prev, openrouter: !prev.openrouter }))}
                        className="p-1 text-slate-400 hover:text-white transition-colors"
                      >
                        {showKeys.openrouter ? (
                          <EyeSlashIcon className="h-4 w-4" />
                        ) : (
                          <EyeIcon className="h-4 w-4" />
                        )}
                      </button>
                      <button
                        type="button"
                        onClick={() => handleTestConnection('openrouter')}
                        disabled={!formData.openrouterApiKey.trim() || testStatuses.find(s => s.service === 'openrouter')?.testing}
                        className="p-1 text-slate-400 hover:text-white disabled:opacity-50 transition-colors"
                      >
                        {testStatuses.find(s => s.service === 'openrouter')?.testing ? (
                          <ArrowPathIcon className="h-4 w-4 animate-spin" />
                        ) : testStatuses.find(s => s.service === 'openrouter')?.result === 'success' ? (
                          <CheckCircleIcon className="h-4 w-4 text-green-400" />
                        ) : testStatuses.find(s => s.service === 'openrouter')?.result === 'failed' ? (
                          <XCircleIcon className="h-4 w-4 text-red-400" />
                        ) : (
                          <InformationCircleIcon className="h-4 w-4" />
                        )}
                      </button>
                    </div>
                  </div>
                  <div className="flex items-center justify-between mt-1">
                    <p className="text-slate-400 text-xs">
                      Get your key from{' '}
                      <a 
                        href="https://openrouter.ai/keys" 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="text-violet-400 hover:text-violet-300 underline"
                      >
                        OpenRouter
                      </a>
                    </p>
                    {testStatuses.find(s => s.service === 'openrouter')?.message && (
                      <p className={`text-xs ${
                        testStatuses.find(s => s.service === 'openrouter')?.result === 'success' ? 'text-green-400' : 'text-red-400'
                      }`}>
                        {testStatuses.find(s => s.service === 'openrouter')?.message}
                      </p>
                    )}
                  </div>
                </div>
              </div>
            </div>

            {/* ClearML Configuration */}
            <div className="space-y-4">
              <div className="flex items-center space-x-3">
                <div className="p-2 bg-purple-500/20 rounded-lg border border-purple-500/30">
                  <CpuChipIcon className="h-5 w-5 text-purple-400" />
                </div>
                <div>
                  <h3 className="text-lg font-medium text-white">ClearML Tracking</h3>
                  <p className="text-slate-400 text-sm">Experiment tracking and model management platform</p>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-slate-300 text-sm font-medium mb-2">
                    Access Key
                  </label>
                  <div className="relative">
                    <input
                      type={showKeys.clearmlAccess ? 'text' : 'password'}
                      value={formData.clearmlAccessKey}
                      onChange={(e) => setFormData(prev => ({ ...prev, clearmlAccessKey: e.target.value }))}
                      placeholder="admin@clearml.com (default)"
                      className="w-full px-3 py-2 pr-10 bg-slate-700/50 border border-slate-600/50 rounded-lg text-white placeholder-slate-400 focus:border-violet-500 focus:outline-none"
                    />
                    <button
                      type="button"
                      onClick={() => setShowKeys(prev => ({ ...prev, clearmlAccess: !prev.clearmlAccess }))}
                      className="absolute right-2 top-1/2 transform -translate-y-1/2 p-1 text-slate-400 hover:text-white transition-colors"
                    >
                      {showKeys.clearmlAccess ? (
                        <EyeSlashIcon className="h-4 w-4" />
                      ) : (
                        <EyeIcon className="h-4 w-4" />
                      )}
                    </button>
                  </div>
                </div>

                <div>
                  <label className="block text-slate-300 text-sm font-medium mb-2">
                    Secret Key
                  </label>
                  <div className="relative">
                    <input
                      type={showKeys.clearmlSecret ? 'text' : 'password'}
                      value={formData.clearmlSecretKey}
                      onChange={(e) => setFormData(prev => ({ ...prev, clearmlSecretKey: e.target.value }))}
                      placeholder="clearml123 (default)"
                      className="w-full px-3 py-2 pr-10 bg-slate-700/50 border border-slate-600/50 rounded-lg text-white placeholder-slate-400 focus:border-violet-500 focus:outline-none"
                    />
                    <button
                      type="button"
                      onClick={() => setShowKeys(prev => ({ ...prev, clearmlSecret: !prev.clearmlSecret }))}
                      className="absolute right-2 top-1/2 transform -translate-y-1/2 p-1 text-slate-400 hover:text-white transition-colors"
                    >
                      {showKeys.clearmlSecret ? (
                        <EyeSlashIcon className="h-4 w-4" />
                      ) : (
                        <EyeIcon className="h-4 w-4" />
                      )}
                    </button>
                  </div>
                </div>
              </div>

              {/* ClearML Test Button */}
              <div className="flex items-center justify-between p-3 bg-slate-700/30 rounded-lg border border-slate-600/30">
                <div className="flex items-center space-x-2">
                  <p className="text-slate-300 text-sm">Test ClearML Connection</p>
                  {testStatuses.find(s => s.service === 'clearml')?.result === 'success' && (
                    <CheckCircleIcon className="h-4 w-4 text-green-400" />
                  )}
                  {testStatuses.find(s => s.service === 'clearml')?.result === 'failed' && (
                    <XCircleIcon className="h-4 w-4 text-red-400" />
                  )}
                </div>
                <button
                  onClick={() => handleTestConnection('clearml')}
                  disabled={
                    !formData.clearmlAccessKey.trim() || 
                    !formData.clearmlSecretKey.trim() || 
                    testStatuses.find(s => s.service === 'clearml')?.testing
                  }
                  className="px-4 py-2 bg-purple-500/20 text-purple-300 rounded-lg hover:bg-purple-500/30 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  {testStatuses.find(s => s.service === 'clearml')?.testing ? 'Testing...' : 'Test Connection'}
                </button>
              </div>

              <div className="flex items-start space-x-3 p-3 bg-blue-500/10 border border-blue-500/20 rounded-lg">
                <InformationCircleIcon className="h-4 w-4 text-blue-400 flex-shrink-0 mt-0.5" />
                <div className="text-xs text-blue-200/80">
                  <p className="font-medium mb-1">Local Development Defaults:</p>
                  <p>Access Key: admin@clearml.com</p>
                  <p>Secret Key: clearml123</p>
                  <p className="mt-1">These work with the local ClearML server started from Settings.</p>
                </div>
              </div>
            </div>

            {/* Storage Options */}
            <div className="space-y-4">
              <div className="flex items-center space-x-3">
                <div className="p-2 bg-orange-500/20 rounded-lg border border-orange-500/30">
                  <ShieldCheckIcon className="h-5 w-5 text-orange-400" />
                </div>
                <div>
                  <h3 className="text-lg font-medium text-white">Storage Preferences</h3>
                  <p className="text-slate-400 text-sm">Choose how to persist your configuration</p>
                </div>
              </div>

              <div className="flex items-center justify-between p-4 bg-slate-700/30 rounded-lg border border-slate-600/30">
                <div>
                  <h4 className="text-white font-medium">Save to Local Storage</h4>
                  <p className="text-slate-400 text-sm">
                    Store API keys in browser localStorage for persistence across sessions
                  </p>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formData.saveToStorage}
                    onChange={(e) => setFormData(prev => ({ ...prev, saveToStorage: e.target.checked }))}
                    className="sr-only peer"
                  />
                  <div className="w-11 h-6 bg-slate-600 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-violet-300/20 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-violet-500"></div>
                </label>
              </div>
            </div>

            {/* Current Status Summary */}
            {serviceStatuses.length > 0 && (
              <div className="space-y-4">
                <h3 className="text-lg font-medium text-white">Current Configuration Status</h3>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  {serviceStatuses.map((status) => (
                    <div
                      key={status.service}
                      className={`p-3 rounded-lg border ${
                        status.configured
                          ? 'bg-green-500/10 border-green-500/20 text-green-300'
                          : 'bg-slate-700/30 border-slate-600/30 text-slate-400'
                      }`}
                    >
                      <div className="flex items-center space-x-2 mb-1">
                        {status.configured ? (
                          <CheckCircleIcon className="h-4 w-4 text-green-400" />
                        ) : (
                          <XCircleIcon className="h-4 w-4 text-slate-500" />
                        )}
                        <span className="font-medium text-sm">{status.service}</span>
                      </div>
                      <p className="text-xs">
                        {status.configured ? 'Configured' : 'Not configured'}
                      </p>
                      {status.lastTested && (
                        <p className="text-xs mt-1 opacity-75">
                          Last tested: {status.lastTested.toLocaleTimeString()}
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="flex items-center justify-between p-6 border-t border-slate-700">
            <button
              onClick={handleClearAll}
              className="px-4 py-2 text-red-400 border border-red-500/30 rounded-lg hover:bg-red-500/10 hover:text-red-300 transition-colors"
            >
              Clear All Keys
            </button>
            
            <div className="flex items-center space-x-3">
              <button
                onClick={onClose}
                className="px-4 py-2 text-slate-400 hover:text-white border border-slate-600/50 rounded-lg hover:border-slate-500 transition-colors"
              >
                Cancel
              </button>
              <motion.button
                onClick={handleSave}
                className="flex items-center space-x-2 px-6 py-2 bg-gradient-to-r from-violet-500 to-purple-500 text-white rounded-lg hover:from-violet-600 hover:to-purple-600 transition-all duration-200"
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
              >
                <ShieldCheckIcon className="h-4 w-4" />
                <span>Save Configuration</span>
              </motion.button>
            </div>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
};

export default EnvironmentSetupModal;