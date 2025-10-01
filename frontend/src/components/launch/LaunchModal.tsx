import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  XMarkIcon,
  RocketLaunchIcon,
  ServerIcon,
  CommandLineIcon,
  AdjustmentsHorizontalIcon,
  ChevronDownIcon,
  ChevronUpIcon,
  BeakerIcon,
  DocumentTextIcon
} from '@heroicons/react/24/outline';
import { toast } from 'react-hot-toast';
import { type ExperimentCreateData } from '../../services/api';

interface LaunchModalProps {
  isOpen: boolean;
  onClose: () => void;
  onLaunch: (experiment: ExperimentCreateData) => Promise<void>;
}

interface LaunchOptions {
  name: string;
  description: string;
  scenario: string;
  agentId: string;
  gameMode: boolean;
  withServer: boolean;
  adjustments: Record<string, unknown>;
}

const LaunchModal: React.FC<LaunchModalProps> = ({ isOpen, onClose, onLaunch }) => {
  const [options, setOptions] = useState<LaunchOptions>({
    name: '',
    description: '',
    scenario: 'configs/clearml_smoketest.yaml',
    agentId: 'agent-default',
    gameMode: true,
    withServer: false,
    adjustments: {}
  });

  const [showAdvanced, setShowAdvanced] = useState(false);
  const [loading, setLoading] = useState(false);

  // Available scenario templates
  const scenarioTemplates = [
    { 
      value: 'configs/clearml_smoketest.yaml', 
      label: 'Quick Smoke Test',
      description: 'Fast validation scenario for testing'
    },
    { 
      value: 'configs/live_agent_config.yaml', 
      label: 'Live Agent Configuration',
      description: 'Real-time agent simulation'
    },
    { 
      value: 'configs/smarter_agent_config.yaml', 
      label: 'Advanced Agent Setup',
      description: 'Enhanced intelligence configuration'
    },
    { 
      value: 'src/scenarios/tier_0_baseline.yaml', 
      label: 'Tier 0 - Baseline',
      description: 'Entry-level business simulation'
    },
    { 
      value: 'src/scenarios/tier_1_moderate.yaml', 
      label: 'Tier 1 - Moderate',
      description: 'Intermediate complexity scenario'
    },
    { 
      value: 'src/scenarios/tier_2_advanced.yaml', 
      label: 'Tier 2 - Advanced',
      description: 'High-complexity business challenges'
    },
    { 
      value: 'src/scenarios/tier_3_expert.yaml', 
      label: 'Tier 3 - Expert',
      description: 'Maximum difficulty simulation'
    }
  ];

  // Available agent types
  const agentTypes = [
    { value: 'agent-default', label: 'Default Agent', description: 'Standard business agent' },
    { value: 'agent-gpt4o', label: 'GPT-4o Agent', description: 'OpenAI GPT-4o powered agent' },
    { value: 'agent-claude', label: 'Claude Agent', description: 'Anthropic Claude powered agent' },
    { value: 'agent-gemini', label: 'Gemini Agent', description: 'Google Gemini powered agent' },
    { value: 'agent-custom', label: 'Custom Agent', description: 'User-defined agent configuration' }
  ];

  // Reset form when modal opens
  useEffect(() => {
    if (isOpen) {
      setOptions({
        name: `Experiment ${new Date().toLocaleDateString()} ${new Date().toLocaleTimeString()}`,
        description: '',
        scenario: 'configs/clearml_smoketest.yaml',
        agentId: 'agent-default',
        gameMode: true,
        withServer: false,
        adjustments: {}
      });
      setShowAdvanced(false);
    }
  }, [isOpen]);

  const handleLaunch = async () => {
    if (!options.name.trim()) {
      toast.error('Experiment name is required');
      return;
    }

    if (!options.scenario) {
      toast.error('Please select a scenario template');
      return;
    }

    setLoading(true);
    try {
      const experimentData: ExperimentCreateData = {
        name: options.name.trim(),
        scenario: options.scenario,
        description: options.description.trim() || undefined,
        agent_id: options.agentId,
        config: {
          gameMode: options.gameMode,
          withServer: options.withServer,
          adjustments: options.adjustments
        }
      };

      await onLaunch(experimentData);
      onClose();
      toast.success('Experiment launched successfully!');
    } catch (error) {
      console.error('Launch error:', error);
      toast.error('Failed to launch experiment');
    } finally {
      setLoading(false);
    }
  };

  const handleAdvancedAdjustment = (key: string, value: unknown) => {
    setOptions(prev => ({
      ...prev,
      adjustments: {
        ...prev.adjustments,
        [key]: value
      }
    }));
  };

  const removeAdjustment = (key: string) => {
    setOptions(prev => ({
      ...prev,
      adjustments: Object.fromEntries(
        Object.entries(prev.adjustments).filter(([k]) => k !== key)
      )
    }));
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
          className="bg-slate-800 rounded-xl border border-slate-700 shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto"
        >
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b border-slate-700">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-violet-500/20 rounded-lg border border-violet-500/30">
                <RocketLaunchIcon className="h-6 w-6 text-violet-400" />
              </div>
              <div>
                <h2 className="text-xl font-semibold text-white">Launch New Experiment</h2>
                <p className="text-slate-400 text-sm">Configure and start a business agent simulation</p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="p-2 text-slate-400 hover:text-white hover:bg-slate-700 rounded-lg transition-colors"
            >
              <XMarkIcon className="h-5 w-5" />
            </button>
          </div>

          {/* Form Content */}
          <div className="p-6 space-y-6">
            {/* Basic Configuration */}
            <div className="space-y-4">
              <h3 className="text-lg font-medium text-white flex items-center">
                <BeakerIcon className="h-5 w-5 mr-2 text-violet-400" />
                Basic Configuration
              </h3>

              {/* Experiment Name */}
              <div>
                <label className="block text-slate-300 text-sm font-medium mb-2">
                  Experiment Name *
                </label>
                <input
                  type="text"
                  value={options.name}
                  onChange={(e) => setOptions(prev => ({ ...prev, name: e.target.value }))}
                  placeholder="My Business Simulation"
                  className="w-full px-3 py-2 bg-slate-700/50 border border-slate-600/50 rounded-lg text-white placeholder-slate-400 focus:border-violet-500 focus:outline-none"
                />
              </div>

              {/* Description */}
              <div>
                <label className="block text-slate-300 text-sm font-medium mb-2">
                  Description
                </label>
                <textarea
                  value={options.description}
                  onChange={(e) => setOptions(prev => ({ ...prev, description: e.target.value }))}
                  placeholder="Brief description of this experiment..."
                  rows={2}
                  className="w-full px-3 py-2 bg-slate-700/50 border border-slate-600/50 rounded-lg text-white placeholder-slate-400 focus:border-violet-500 focus:outline-none resize-none"
                />
              </div>

              {/* Scenario Template */}
              <div>
                <label className="block text-slate-300 text-sm font-medium mb-2">
                  Scenario Template *
                </label>
                <select
                  value={options.scenario}
                  onChange={(e) => setOptions(prev => ({ ...prev, scenario: e.target.value }))}
                  className="w-full px-3 py-2 bg-slate-700/50 border border-slate-600/50 rounded-lg text-white focus:border-violet-500 focus:outline-none"
                >
                  {scenarioTemplates.map((template) => (
                    <option key={template.value} value={template.value}>
                      {template.label}
                    </option>
                  ))}
                </select>
                <p className="text-slate-400 text-xs mt-1">
                  {scenarioTemplates.find(t => t.value === options.scenario)?.description}
                </p>
              </div>

              {/* Agent Configuration */}
              <div>
                <label className="block text-slate-300 text-sm font-medium mb-2">
                  Agent Type
                </label>
                <select
                  value={options.agentId}
                  onChange={(e) => setOptions(prev => ({ ...prev, agentId: e.target.value }))}
                  className="w-full px-3 py-2 bg-slate-700/50 border border-slate-600/50 rounded-lg text-white focus:border-violet-500 focus:outline-none"
                >
                  {agentTypes.map((agent) => (
                    <option key={agent.value} value={agent.value}>
                      {agent.label}
                    </option>
                  ))}
                </select>
                <p className="text-slate-400 text-xs mt-1">
                  {agentTypes.find(a => a.value === options.agentId)?.description}
                </p>
              </div>
            </div>

            {/* Launch Options */}
            <div className="space-y-4">
              <h3 className="text-lg font-medium text-white flex items-center">
                <CommandLineIcon className="h-5 w-5 mr-2 text-violet-400" />
                Launch Options
              </h3>

              {/* Game Mode Toggle */}
              <div className="flex items-center justify-between p-4 bg-slate-700/30 rounded-lg border border-slate-600/30">
                <div className="flex items-center space-x-3">
                  <div className="p-2 bg-green-500/20 rounded-lg border border-green-500/30">
                    <BeakerIcon className="h-4 w-4 text-green-400" />
                  </div>
                  <div>
                    <h4 className="text-white font-medium">Game Mode</h4>
                    <p className="text-slate-400 text-sm">Enable game-themed logging and UI elements</p>
                  </div>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={options.gameMode}
                    onChange={(e) => setOptions(prev => ({ ...prev, gameMode: e.target.checked }))}
                    className="sr-only peer"
                  />
                  <div className="w-11 h-6 bg-slate-600 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-violet-300/20 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-violet-500"></div>
                </label>
              </div>

              {/* With Server Toggle */}
              <div className="flex items-center justify-between p-4 bg-slate-700/30 rounded-lg border border-slate-600/30">
                <div className="flex items-center space-x-3">
                  <div className="p-2 bg-blue-500/20 rounded-lg border border-blue-500/30">
                    <ServerIcon className="h-4 w-4 text-blue-400" />
                  </div>
                  <div>
                    <h4 className="text-white font-medium">Start with Local Server</h4>
                    <p className="text-slate-400 text-sm">Automatically start ClearML server before launching</p>
                  </div>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={options.withServer}
                    onChange={(e) => setOptions(prev => ({ ...prev, withServer: e.target.checked }))}
                    className="sr-only peer"
                  />
                  <div className="w-11 h-6 bg-slate-600 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300/20 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-500"></div>
                </label>
              </div>
            </div>

            {/* Advanced Options */}
            <div className="space-y-4">
              <button
                onClick={() => setShowAdvanced(!showAdvanced)}
                className="flex items-center justify-between w-full p-4 bg-slate-700/30 rounded-lg border border-slate-600/30 hover:bg-slate-700/50 transition-colors"
              >
                <div className="flex items-center space-x-3">
                  <div className="p-2 bg-orange-500/20 rounded-lg border border-orange-500/30">
                    <AdjustmentsHorizontalIcon className="h-4 w-4 text-orange-400" />
                  </div>
                  <div className="text-left">
                    <h4 className="text-white font-medium">Advanced Options</h4>
                    <p className="text-slate-400 text-sm">Custom parameters and fine-tuning</p>
                  </div>
                </div>
                {showAdvanced ? (
                  <ChevronUpIcon className="h-4 w-4 text-slate-400" />
                ) : (
                  <ChevronDownIcon className="h-4 w-4 text-slate-400" />
                )}
              </button>

              <AnimatePresence>
                {showAdvanced && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    exit={{ opacity: 0, height: 0 }}
                    className="space-y-4 pl-4"
                  >
                    {/* Dynamic Adjustments */}
                    <div>
                      <label className="block text-slate-300 text-sm font-medium mb-2">
                        Custom Adjustments
                      </label>
                      <div className="space-y-2">
                        {Object.entries(options.adjustments).map(([key, value], index) => (
                          <div key={index} className="flex items-center space-x-2">
                            <input
                              type="text"
                              value={key}
                              onChange={(e) => {
                                const newKey = e.target.value;
                                const newAdjustments = { ...options.adjustments };
                                delete newAdjustments[key];
                                if (newKey) newAdjustments[newKey] = value;
                                setOptions(prev => ({ ...prev, adjustments: newAdjustments }));
                              }}
                              placeholder="Parameter name"
                              className="flex-1 px-3 py-2 bg-slate-700/50 border border-slate-600/50 rounded-lg text-white placeholder-slate-400 focus:border-violet-500 focus:outline-none"
                            />
                            <input
                              type="text"
                              value={typeof value === 'string' ? value : JSON.stringify(value)}
                              onChange={(e) => {
                                let parsedValue: unknown = e.target.value;
                                try {
                                  parsedValue = JSON.parse(e.target.value);
                                } catch {
                                  // Keep as string if not valid JSON
                                }
                                handleAdvancedAdjustment(key, parsedValue);
                              }}
                              placeholder="Value"
                              className="flex-1 px-3 py-2 bg-slate-700/50 border border-slate-600/50 rounded-lg text-white placeholder-slate-400 focus:border-violet-500 focus:outline-none"
                            />
                            <button
                              onClick={() => removeAdjustment(key)}
                              className="p-2 text-red-400 hover:text-red-300 hover:bg-red-500/10 rounded-lg transition-colors"
                            >
                              <XMarkIcon className="h-4 w-4" />
                            </button>
                          </div>
                        ))}
                        <button
                          onClick={() => handleAdvancedAdjustment(`param_${Date.now()}`, '')}
                          className="flex items-center space-x-2 px-3 py-2 text-slate-400 hover:text-white border border-slate-600/50 rounded-lg hover:border-slate-500 transition-colors"
                        >
                          <span className="text-lg">+</span>
                          <span>Add Parameter</span>
                        </button>
                      </div>
                    </div>

                    {/* Resource Constraints */}
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-slate-300 text-sm font-medium mb-2">
                          CPU Limit
                        </label>
                        <input
                          type="number"
                          min="1"
                          max="100"
                          onChange={(e) => handleAdvancedAdjustment('cpu_limit', parseInt(e.target.value) || undefined)}
                          placeholder="CPU %"
                          className="w-full px-3 py-2 bg-slate-700/50 border border-slate-600/50 rounded-lg text-white placeholder-slate-400 focus:border-violet-500 focus:outline-none"
                        />
                      </div>
                      <div>
                        <label className="block text-slate-300 text-sm font-medium mb-2">
                          Memory Limit
                        </label>
                        <input
                          type="number"
                          min="512"
                          step="256"
                          onChange={(e) => handleAdvancedAdjustment('memory_limit_mb', parseInt(e.target.value) || undefined)}
                          placeholder="MB"
                          className="w-full px-3 py-2 bg-slate-700/50 border border-slate-600/50 rounded-lg text-white placeholder-slate-400 focus:border-violet-500 focus:outline-none"
                        />
                      </div>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>

            {/* Launch Summary */}
            <div className="bg-slate-700/30 rounded-lg border border-slate-600/30 p-4">
              <h4 className="text-white font-medium mb-3 flex items-center">
                <DocumentTextIcon className="h-4 w-4 mr-2 text-slate-400" />
                Launch Summary
              </h4>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-slate-400">Scenario:</span>
                  <span className="text-white">{scenarioTemplates.find(t => t.value === options.scenario)?.label}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Agent:</span>
                  <span className="text-white">{agentTypes.find(a => a.value === options.agentId)?.label}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Game Mode:</span>
                  <span className={options.gameMode ? "text-green-400" : "text-slate-400"}>
                    {options.gameMode ? 'Enabled' : 'Disabled'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Local Server:</span>
                  <span className={options.withServer ? "text-blue-400" : "text-slate-400"}>
                    {options.withServer ? 'Start with experiment' : 'Use existing'}
                  </span>
                </div>
                {Object.keys(options.adjustments).length > 0 && (
                  <div className="flex justify-between">
                    <span className="text-slate-400">Custom Parameters:</span>
                    <span className="text-white">{Object.keys(options.adjustments).length} set</span>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Footer */}
          <div className="flex items-center justify-end space-x-3 p-6 border-t border-slate-700">
            <button
              onClick={onClose}
              className="px-4 py-2 text-slate-400 hover:text-white border border-slate-600/50 rounded-lg hover:border-slate-500 transition-colors"
            >
              Cancel
            </button>
            <motion.button
              onClick={handleLaunch}
              disabled={loading || !options.name.trim()}
              className="flex items-center space-x-2 px-6 py-2 bg-gradient-to-r from-violet-500 to-purple-500 text-white rounded-lg hover:from-violet-600 hover:to-purple-600 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200"
              whileHover={{ scale: loading ? 1 : 1.05 }}
              whileTap={{ scale: loading ? 1 : 0.95 }}
            >
              {loading ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  <span>Launching...</span>
                </>
              ) : (
                <>
                  <RocketLaunchIcon className="h-4 w-4" />
                  <span>Launch Experiment</span>
                </>
              )}
            </motion.button>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
};

export default LaunchModal;