import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  DocumentTextIcon,
  PlayIcon,
  AdjustmentsHorizontalIcon,
  EyeIcon,
  PencilIcon,
  CheckIcon,
  XMarkIcon,
  FolderIcon,
  CogIcon
} from '@heroicons/react/24/outline';
import { apiService } from '../services/api';
import { toast } from 'react-hot-toast';

// Type definition for template adjustments
type TemplateAdjustments = Record<string, string | number | boolean>;

interface SuccessCriteria {
  profit_target_min?: number;
  on_time_delivery_rate?: number;
  customer_satisfaction?: number;
}

interface AgentConstraints {
  initial_capital?: number;
  max_debt_ratio?: number;
}

interface MarketConditions {
  base_demand_index?: number;
  competition_level?: string;
  seasonality?: string;
}

interface LLMConfig {
  client_type?: string;
  model?: string;
  temperature?: number;
  max_tokens?: number;
}

interface AgentConfig {
  name?: string;
  description?: string;
  agent_class?: string;
  llm_config?: LLMConfig;
  memory?: {
    enabled?: boolean;
    max_entries?: number;
  };
}

interface ParsedTemplate {
  scenario_name?: string;
  scenario_type?: string;
  difficulty_tier?: number;
  expected_duration?: number;
  description?: string;
  success_criteria?: SuccessCriteria;
  agent_constraints?: AgentConstraints;
  market_conditions?: MarketConditions;
  agent?: AgentConfig;
}

interface Template {
  name: string;
  path: string;
  content: string;
  parsed: ParsedTemplate;
  size: number;
  modified: string;
}

interface TemplateCardProps {
  template: Template;
  onView: (template: Template) => void;
  onEdit: (template: Template) => void;
  onRun: (template: Template) => void;
}

const TemplateCard: React.FC<TemplateCardProps> = ({ template, onView, onEdit, onRun }) => {
  const getTemplateIcon = (name: string) => {
    if (name.includes('smoketest')) return '🧪';
    if (name.includes('live')) return '🚀';
    if (name.includes('model')) return '🤖';
    if (name.includes('simulation')) return '⚙️';
    return '📄';
  };

  const getDifficultyLevel = (parsed: ParsedTemplate) => {
    const tier = parsed?.difficulty_tier || 0;
    if (tier === 0) return { label: 'Beginner', color: 'text-green-400 bg-green-400/10 border-green-400/30' };
    if (tier === 1) return { label: 'Intermediate', color: 'text-yellow-400 bg-yellow-400/10 border-yellow-400/30' };
    if (tier === 2) return { label: 'Advanced', color: 'text-orange-400 bg-orange-400/10 border-orange-400/30' };
    if (tier >= 3) return { label: 'Expert', color: 'text-red-400 bg-red-400/10 border-red-400/30' };
    return { label: 'Unknown', color: 'text-slate-400 bg-slate-400/10 border-slate-400/30' };
  };

  const difficulty = getDifficultyLevel(template.parsed);

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      className="bg-slate-800/50 backdrop-blur-sm rounded-xl border border-slate-700/50 p-6 hover:border-slate-600/50 transition-all duration-200"
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-start space-x-3">
          <div className="text-3xl">{getTemplateIcon(template.name)}</div>
          <div>
            <h3 className="text-white font-semibold text-lg">{template.name}</h3>
            <p className="text-slate-400 text-sm">
              {template.parsed?.scenario_name || 'Scenario Template'}
            </p>
            <div className="flex items-center space-x-3 mt-2">
              <span className={`px-2 py-1 text-xs rounded-full border ${difficulty.color}`}>
                {difficulty.label}
              </span>
              <span className="text-slate-500 text-xs">
                {(template.size / 1024).toFixed(1)}KB
              </span>
            </div>
          </div>
        </div>
        
        <div className="flex items-center space-x-2">
          <button
            onClick={() => onView(template)}
            className="p-2 text-slate-400 hover:text-white hover:bg-slate-700/50 rounded-lg transition-colors"
            title="View Template"
          >
            <EyeIcon className="h-4 w-4" />
          </button>
          <button
            onClick={() => onEdit(template)}
            className="p-2 text-slate-400 hover:text-blue-400 hover:bg-blue-500/10 rounded-lg transition-colors"
            title="Edit Template"
          >
            <PencilIcon className="h-4 w-4" />
          </button>
          <button
            onClick={() => onRun(template)}
            className="p-2 text-green-400 hover:text-green-300 hover:bg-green-500/10 rounded-lg transition-colors"
            title="Run Template"
          >
            <PlayIcon className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Template Info */}
      {template.parsed && (
        <div className="space-y-3">
          {template.parsed.description && (
            <p className="text-slate-300 text-sm">{template.parsed.description}</p>
          )}
          
          <div className="grid grid-cols-2 gap-4 text-sm">
            {template.parsed.expected_duration && (
              <div>
                <span className="text-slate-400">Duration:</span>
                <span className="text-white ml-2">{template.parsed.expected_duration} ticks</span>
              </div>
            )}
            {template.parsed.scenario_type && (
              <div>
                <span className="text-slate-400">Type:</span>
                <span className="text-white ml-2">{template.parsed.scenario_type}</span>
              </div>
            )}
          </div>

          {/* Success Criteria */}
          {template.parsed.success_criteria && (
            <div className="mt-3 p-3 bg-slate-700/30 rounded-lg">
              <h4 className="text-slate-300 font-medium text-sm mb-2">Success Criteria</h4>
              <div className="grid grid-cols-1 gap-1 text-xs">
                {Object.entries(template.parsed.success_criteria).map(([key, value]) => (
                  <div key={key} className="flex justify-between">
                    <span className="text-slate-400">{key.replace(/_/g, ' ')}:</span>
                    <span className="text-white">{String(value)}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </motion.div>
  );
};

interface TemplateViewerProps {
  template: Template | null;
  onClose: () => void;
}

const TemplateViewer: React.FC<TemplateViewerProps> = ({ template, onClose }) => {
  if (!template) return null;

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
      onClick={onClose}
    >
      <motion.div
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.9, opacity: 0 }}
        className="bg-slate-800 rounded-xl border border-slate-700 p-6 max-w-4xl w-full max-h-[80vh] overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-white font-semibold text-lg flex items-center">
            <DocumentTextIcon className="h-5 w-5 mr-2" />
            {template.name}
          </h3>
          <button
            onClick={onClose}
            className="p-2 text-slate-400 hover:text-white hover:bg-slate-700/50 rounded-lg transition-colors"
          >
            <XMarkIcon className="h-5 w-5" />
          </button>
        </div>
        
        <div className="overflow-auto max-h-[60vh]">
          <pre className="text-sm text-slate-300 bg-slate-900/50 p-4 rounded-lg overflow-x-auto">
            {template.content}
          </pre>
        </div>
      </motion.div>
    </motion.div>
  );
};

interface TemplateEditorProps {
  template: Template | null;
  onClose: () => void;
  onSave: (template: Template, adjustments: TemplateAdjustments) => void;
}

const TemplateEditor: React.FC<TemplateEditorProps> = ({ template, onClose, onSave }) => {
  const [adjustments, setAdjustments] = useState<TemplateAdjustments>({});
  const [activeTab, setActiveTab] = useState<'parameters' | 'raw'>('parameters');

  if (!template) return null;

  const handleAdjustmentChange = (key: string, value: string | number | boolean) => {
    setAdjustments((prev: TemplateAdjustments) => ({ ...prev, [key]: value }));
  };

  const handleSave = () => {
    onSave(template, adjustments);
  };

  // Extract editable parameters from template
  const getEditableParams = (parsed: ParsedTemplate) => {
    const params: Array<{ key: string; value: string | number | boolean; type: 'string' | 'number' | 'boolean'; description?: string }> = [];
    
    if (parsed?.expected_duration) {
      params.push({
        key: 'expected_duration',
        value: parsed.expected_duration,
        type: 'number',
        description: 'Number of simulation ticks to run'
      });
    }
    
    if (parsed?.agent_constraints?.initial_capital) {
      params.push({
        key: 'agent_constraints.initial_capital',
        value: parsed.agent_constraints.initial_capital,
        type: 'number',
        description: 'Starting capital for the agent'
      });
    }
    
    if (parsed?.market_conditions?.base_demand_index) {
      params.push({
        key: 'market_conditions.base_demand_index',
        value: parsed.market_conditions.base_demand_index,
        type: 'number',
        description: 'Base market demand multiplier'
      });
    }
    
    if (parsed?.success_criteria?.profit_target_min) {
      params.push({
        key: 'success_criteria.profit_target_min',
        value: parsed.success_criteria.profit_target_min,
        type: 'number',
        description: 'Minimum profit target for success'
      });
    }

    return params;
  };

  const editableParams = getEditableParams(template.parsed);

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
      onClick={onClose}
    >
      <motion.div
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.9, opacity: 0 }}
        className="bg-slate-800 rounded-xl border border-slate-700 p-6 max-w-4xl w-full max-h-[80vh] overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-white font-semibold text-lg flex items-center">
            <AdjustmentsHorizontalIcon className="h-5 w-5 mr-2" />
            Adjust Template: {template.name}
          </h3>
          <div className="flex items-center space-x-2">
            <button
              onClick={handleSave}
              className="flex items-center space-x-2 px-4 py-2 bg-green-500/20 text-green-300 rounded-lg hover:bg-green-500/30 transition-colors"
            >
              <CheckIcon className="h-4 w-4" />
              <span>Save & Run</span>
            </button>
            <button
              onClick={onClose}
              className="p-2 text-slate-400 hover:text-white hover:bg-slate-700/50 rounded-lg transition-colors"
            >
              <XMarkIcon className="h-5 w-5" />
            </button>
          </div>
        </div>
        
        {/* Tabs */}
        <div className="flex space-x-1 mb-4">
          <button
            onClick={() => setActiveTab('parameters')}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              activeTab === 'parameters'
                ? 'bg-violet-500/20 text-violet-300 border border-violet-500/30'
                : 'text-slate-400 hover:text-slate-300'
            }`}
          >
            Parameters
          </button>
          <button
            onClick={() => setActiveTab('raw')}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              activeTab === 'raw'
                ? 'bg-violet-500/20 text-violet-300 border border-violet-500/30'
                : 'text-slate-400 hover:text-slate-300'
            }`}
          >
            Raw YAML
          </button>
        </div>

        <div className="overflow-auto max-h-[50vh]">
          {activeTab === 'parameters' ? (
            <div className="space-y-4">
              {editableParams.length > 0 ? (
                editableParams.map((param) => (
                  <div key={param.key} className="space-y-2">
                    <label className="block text-slate-300 text-sm font-medium">
                      {param.key.split('.').pop()?.replace(/_/g, ' ')}
                    </label>
                    {param.description && (
                      <p className="text-slate-400 text-xs">{param.description}</p>
                    )}
                    {param.type === 'boolean' ? (
                      <label className="flex items-center space-x-3 cursor-pointer">
                        <input
                          type="checkbox"
                          defaultChecked={Boolean(param.value)}
                          onChange={(e) => {
                            handleAdjustmentChange(param.key, e.target.checked);
                          }}
                          className="w-4 h-4 text-violet-600 bg-slate-700 border-slate-600 rounded focus:ring-violet-500 focus:ring-2"
                        />
                        <span className="text-slate-300 text-sm">
                          {Boolean(param.value) ? 'Enabled' : 'Disabled'}
                        </span>
                      </label>
                    ) : (
                      <input
                        type={param.type === 'number' ? 'number' : 'text'}
                        defaultValue={String(param.value)}
                        onChange={(e) => {
                          let value: string | number | boolean;
                          if (param.type === 'number') {
                            value = parseFloat(e.target.value) || 0;
                          } else {
                            value = e.target.value;
                          }
                          handleAdjustmentChange(param.key, value);
                        }}
                        className="w-full px-3 py-2 bg-slate-700/50 border border-slate-600/50 rounded-lg text-white focus:border-violet-500 focus:outline-none"
                      />
                    )}
                  </div>
                ))
              ) : (
                <div className="text-center py-8">
                  <CogIcon className="h-12 w-12 text-slate-600 mx-auto mb-4" />
                  <p className="text-slate-400">No editable parameters found in this template</p>
                  <p className="text-slate-500 text-sm mt-2">You can still run it as-is or edit the raw YAML</p>
                </div>
              )}
            </div>
          ) : (
            <div>
              <pre className="text-sm text-slate-300 bg-slate-900/50 p-4 rounded-lg overflow-x-auto">
                {template.content}
              </pre>
            </div>
          )}
        </div>
      </motion.div>
    </motion.div>
  );
};

const Templates: React.FC = () => {
  const [templates, setTemplates] = useState<Template[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedTemplate, setSelectedTemplate] = useState<Template | null>(null);
  const [editingTemplate, setEditingTemplate] = useState<Template | null>(null);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    loadTemplates();
  }, []);

  const loadTemplates = async () => {
    try {
      setLoading(true);
      
      // Get available templates
      const response = await apiService.get<{ templates: Template[] }>('/api/v1/templates');
      setTemplates(response.data.templates || []);
      
    } catch (error) {
      console.error('Failed to load templates:', error);
      
      // Use mock data for development
      const mockTemplates: Template[] = [
        {
          name: 'clearml_smoketest.yaml',
          path: 'configs/clearml_smoketest.yaml',
          content: `# ClearML smoke test scenario for ScenarioEngine

scenario_name: ClearML_SmokeTest
scenario_type: single_agent
difficulty_tier: 0
expected_duration: 10
deterministic_profit_shaping: true

success_criteria:
  profit_target_min: 100.0
  on_time_delivery_rate: 0.90
  customer_satisfaction: 0.75

market_conditions:
  base_demand_index: 1.0
  competition_level: low
  seasonality: stable

business_parameters:
  product_categories:
    - general_merchandise
  supply_chain_complexity: low
  pricing_strategy: fixed

external_events:
  - name: "minor_marketing_boost"
    tick: 5
    type: "marketing_campaign"
    impact:
      market_share_delta: 0.02

agent_constraints:
  initial_capital: 50000
  max_debt_ratio: 0.8`,
          parsed: {
            scenario_name: 'ClearML_SmokeTest',
            scenario_type: 'single_agent',
            difficulty_tier: 0,
            expected_duration: 10,
            success_criteria: {
              profit_target_min: 100.0,
              on_time_delivery_rate: 0.90,
              customer_satisfaction: 0.75
            },
            agent_constraints: {
              initial_capital: 50000,
              max_debt_ratio: 0.8
            },
            market_conditions: {
              base_demand_index: 1.0
            }
          },
          size: 856,
          modified: new Date().toISOString()
        },
        {
          name: 'live_agent_config.yaml',
          path: 'configs/live_agent_config.yaml',
          content: `# Configuration for a live, API-driven agent
agent:
  name: "Baseline API Agent v1"
  description: "A simple agent that uses a live LLM for basic decision-making."
  agent_class: "benchmarking.agents.unified_agent.UnifiedAgent"
  llm_config:
    client_type: "openai"
    model: "gpt-4o"
    temperature: 0.5
    max_tokens: 1500
  memory:
    enabled: true
    max_entries: 100`,
          parsed: {
            agent: {
              name: 'Baseline API Agent v1',
              description: 'A simple agent that uses a live LLM for basic decision-making.',
              llm_config: {
                model: 'gpt-4o',
                temperature: 0.5,
                max_tokens: 1500
              }
            }
          },
          size: 312,
          modified: new Date().toISOString()
        }
      ];
      
      setTemplates(mockTemplates);
      toast.error('Failed to load templates from API, using mock data');
    } finally {
      setLoading(false);
    }
  };

  const handleRunTemplate = async (template: Template, adjustments?: TemplateAdjustments) => {
    try {
      toast.loading('Starting experiment with template...', { id: 'run-template' });
      
      // Create experiment using the template
      const experimentData = {
        name: `${template.parsed?.scenario_name || template.name} - ${Date.now()}`,
        scenario: template.path,
        config: {
          gameMode: true,
          adjustments: adjustments || {}
        }
      };

      await apiService.createExperiment(experimentData);
      
      toast.success('Experiment started successfully!', { id: 'run-template' });
      
      // Navigate to experiments page
      window.location.href = '/experiments';
      
    } catch (error) {
      console.error('Failed to run template:', error);
      toast.error('Failed to start experiment', { id: 'run-template' });
    }
  };

  const handleSaveAndRun = (template: Template, adjustments: TemplateAdjustments) => {
    setEditingTemplate(null);
    handleRunTemplate(template, adjustments);
  };

  const filteredTemplates = templates.filter(template => 
    template.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    template.parsed?.scenario_name?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center justify-between mb-8"
      >
        <div>
          <h1 className="text-3xl font-bold bg-gradient-to-r from-violet-400 to-purple-400 bg-clip-text text-transparent">
            Scenario Templates
          </h1>
          <p className="text-slate-400 mt-2">Browse, customize, and run simulation templates</p>
        </div>
        
        <div className="flex items-center space-x-4">
          <input
            type="text"
            placeholder="Search templates..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="px-4 py-2 bg-slate-700/50 border border-slate-600/50 rounded-lg text-white placeholder-slate-400 focus:border-violet-500 focus:outline-none"
          />
          
          <button
            onClick={loadTemplates}
            className="flex items-center space-x-2 px-4 py-2 bg-slate-700/50 text-slate-300 rounded-lg hover:bg-slate-700 transition-colors"
          >
            <FolderIcon className="h-4 w-4" />
            <span>Refresh</span>
          </button>
        </div>
      </motion.div>

      {/* Templates Grid */}
      {loading ? (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-violet-400"></div>
        </div>
      ) : filteredTemplates.length > 0 ? (
        <motion.div
          className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
        >
          <AnimatePresence>
            {filteredTemplates.map((template) => (
              <TemplateCard
                key={template.path}
                template={template}
                onView={setSelectedTemplate}
                onEdit={setEditingTemplate}
                onRun={(t) => handleRunTemplate(t)}
              />
            ))}
          </AnimatePresence>
        </motion.div>
      ) : (
        <motion.div
          className="text-center py-12"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
        >
          <DocumentTextIcon className="h-16 w-16 text-slate-600 mx-auto mb-6" />
          <h3 className="text-xl font-semibold text-slate-300 mb-4">No Templates Found</h3>
          <p className="text-slate-400 mb-8 max-w-md mx-auto">
            No scenario templates were found. Make sure templates are available in the configs directory.
          </p>
          
          <div className="space-y-4 max-w-md mx-auto">
            <button
              onClick={loadTemplates}
              className="w-full flex items-center justify-center space-x-2 px-6 py-3 bg-gradient-to-r from-violet-500 to-purple-500 text-white rounded-lg hover:from-violet-600 hover:to-purple-600 transition-all duration-200"
            >
              <FolderIcon className="h-5 w-5" />
              <span>Reload Templates</span>
            </button>
          </div>
          
          <div className="mt-8 p-6 bg-slate-800/30 rounded-lg border border-slate-700/30">
            <h4 className="text-white font-medium mb-3">Template Guidelines:</h4>
            <ul className="text-slate-400 text-sm space-y-2 text-left">
              <li>• Templates should be YAML files in the configs directory</li>
              <li>• Include scenario_name, difficulty_tier, and expected_duration</li>
              <li>• Define success_criteria and agent_constraints</li>
              <li>• Use the CLI command <code className="text-violet-400">fba-bench run-template</code> to test</li>
            </ul>
          </div>
        </motion.div>
      )}

      {/* Template Viewer Modal */}
      <AnimatePresence>
        {selectedTemplate && (
          <TemplateViewer
            template={selectedTemplate}
            onClose={() => setSelectedTemplate(null)}
          />
        )}
      </AnimatePresence>

      {/* Template Editor Modal */}
      <AnimatePresence>
        {editingTemplate && (
          <TemplateEditor
            template={editingTemplate}
            onClose={() => setEditingTemplate(null)}
            onSave={handleSaveAndRun}
          />
        )}
      </AnimatePresence>
    </div>
  );
};

export default Templates;