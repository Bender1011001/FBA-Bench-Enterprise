import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  BeakerIcon,
  StopIcon,
  DocumentDuplicateIcon,
  TrashIcon,
  EyeIcon,
  ClockIcon,
  CheckCircleIcon,
  XCircleIcon,
  FunnelIcon,
  RocketLaunchIcon
} from '@heroicons/react/24/outline';
import { apiService, type ExperimentCreateData, type Experiment } from '../services/api';
import { useAppStore } from '../store/appStore';
import { toast } from 'react-hot-toast';
import LaunchModal from '../components/launch/LaunchModal';

interface ExperimentCardProps {
  experiment: Experiment;
  onView: (id: string) => void;
  onClone: (id: string) => void;
  onStop: (id: string) => void;
  onDelete: (id: string) => void;
}

const ExperimentCard: React.FC<ExperimentCardProps> = ({ 
  experiment, 
  onView, 
  onClone, 
  onStop, 
  onDelete 
}) => {
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed': return CheckCircleIcon;
      case 'running': return ClockIcon;
      case 'failed': return XCircleIcon;
      default: return ClockIcon;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'text-green-400 bg-green-400/10 border-green-400/30';
      case 'running': return 'text-blue-400 bg-blue-400/10 border-blue-400/30';
      case 'failed': return 'text-red-400 bg-red-400/10 border-red-400/30';
      default: return 'text-yellow-400 bg-yellow-400/10 border-yellow-400/30';
    }
  };

  const StatusIcon = getStatusIcon(experiment.status);

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
          <div className={`p-2 rounded-lg border ${getStatusColor(experiment.status)}`}>
            <StatusIcon className="h-5 w-5" />
          </div>
          <div>
            <h3 className="text-white font-semibold text-lg">{experiment.name}</h3>
            <p className="text-slate-400 text-sm">
              Created {new Date(experiment.created).toLocaleDateString()}
            </p>
          </div>
        </div>
        
        <div className="flex items-center space-x-2">
          <button
            onClick={() => onView(experiment.id)}
            className="p-2 text-slate-400 hover:text-white hover:bg-slate-700/50 rounded-lg transition-colors"
          >
            <EyeIcon className="h-4 w-4" />
          </button>
          <button
            onClick={() => onClone(experiment.id)}
            className="p-2 text-slate-400 hover:text-white hover:bg-slate-700/50 rounded-lg transition-colors"
          >
            <DocumentDuplicateIcon className="h-4 w-4" />
          </button>
          {experiment.status === 'running' && (
            <button
              onClick={() => onStop(experiment.id)}
              className="p-2 text-orange-400 hover:text-orange-300 hover:bg-orange-500/10 rounded-lg transition-colors"
            >
              <StopIcon className="h-4 w-4" />
            </button>
          )}
          <button
            onClick={() => onDelete(experiment.id)}
            className="p-2 text-red-400 hover:text-red-300 hover:bg-red-500/10 rounded-lg transition-colors"
          >
            <TrashIcon className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Metrics */}
      {experiment.metrics && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
          <div className="text-center">
            <p className="text-slate-400 text-xs">Profit</p>
            <p className="text-green-400 font-semibold">
              ${experiment.metrics.profit?.toLocaleString() || 'N/A'}
            </p>
          </div>
          <div className="text-center">
            <p className="text-slate-400 text-xs">Market Share</p>
            <p className="text-blue-400 font-semibold">
              {experiment.metrics.marketShare?.toFixed(1) || 'N/A'}%
            </p>
          </div>
          <div className="text-center">
            <p className="text-slate-400 text-xs">Satisfaction</p>
            <p className="text-purple-400 font-semibold">
              {experiment.metrics.satisfaction?.toFixed(1) || 'N/A'}%
            </p>
          </div>
          <div className="text-center">
            <p className="text-slate-400 text-xs">Score</p>
            <p className="text-yellow-400 font-semibold">
              {experiment.metrics.score?.toFixed(0) || 'N/A'}
            </p>
          </div>
        </div>
      )}

      {/* Progress Bar */}
      <div className="w-full bg-slate-700 rounded-full h-2 mb-4">
        <motion.div
          className="bg-gradient-to-r from-violet-500 to-purple-500 h-2 rounded-full"
          initial={{ width: 0 }}
          animate={{ width: `${experiment.progress || 0}%` }}
          transition={{ duration: 1, ease: "easeOut" }}
        />
      </div>

      {/* Tags */}
      {experiment.tags && experiment.tags.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {experiment.tags.map((tag: string, index: number) => (
            <span
              key={index}
              className="px-2 py-1 bg-violet-500/20 text-violet-300 text-xs rounded-full border border-violet-500/30"
            >
              {tag}
            </span>
          ))}
        </div>
      )}
    </motion.div>
  );
};

function normalizeExperiments(input: unknown): Experiment[] {
  // Accepts arrays, envelopes { items: [] } or { experiments: [] }, keyed maps, and strings.
  // Always returns a flat Experiment[].
  if (Array.isArray(input)) {
    // Flatten nested arrays: e.g., [ [exp1, exp2] ] -> [exp1, exp2]
    return (input as unknown[]).flatMap((v) =>
      Array.isArray(v) ? (v as Experiment[]) : [v as Experiment]
    );
  }
  if (typeof input === "string") {
    try {
      return normalizeExperiments(JSON.parse(input));
    } catch {
      return [];
    }
  }
  if (input && typeof input === "object") {
    const obj = input as Record<string, unknown>;
    const items = (obj as { items?: unknown }).items;
    if (Array.isArray(items)) return items as Experiment[];

    const experiments = (obj as { experiments?: unknown }).experiments;
    if (Array.isArray(experiments)) return experiments as Experiment[];

    // Keyed map { [id]: Experiment } -> values
    return Object.values(obj) as Experiment[];
  }
  return [];
}

const Experiments: React.FC = () => {
  const { experiments: experimentsState, loading, filters, setExperiments, setLoading, setFilters } = useAppStore();

  // Ensure any incidental references to `experiments` within this component scope
  // always point to a normalized array. This guards against stale bundles or
  // accidental direct uses of a non-array value.
  const experiments: Experiment[] =
    Array.isArray(experimentsState)
      ? experimentsState
      : experimentsState && typeof experimentsState === "object" && !("length" in experimentsState)
        ? Object.values(experimentsState as Record<string, Experiment>)
        : [];
  const [showFilters, setShowFilters] = useState(false);
  const [showLaunchModal, setShowLaunchModal] = useState(false);

  useEffect(() => {
    loadExperiments();
  }, [filters]);

  const loadExperiments = async () => {
    try {
      setLoading('experiments', true);
      const response = await apiService.getExperiments(filters.project);
      console.log('API response for experiments:', response);
      console.log('response.data:', response.data);
      console.log('response.data type:', typeof response.data);
      console.log('Is response.data array?', Array.isArray(response.data));
      const normalized = normalizeExperiments(response.data as unknown);
      console.log('Normalized experiments length:', normalized.length);
      setExperiments(normalized);
    } catch (error) {
      toast.error('Failed to load experiments');
      console.error('Load experiments error:', error);
    } finally {
      setLoading('experiments', false);
    }
  };

  const handleLaunchExperiment = async (experimentData: ExperimentCreateData) => {
    try {
      toast.loading('Launching experiment...', { id: 'launch-exp' });
      
      // If withServer is enabled, start ClearML first
      if (experimentData.config.withServer) {
        toast.loading('Starting ClearML server...', { id: 'launch-exp' });
        await apiService.startClearMLStack();
        toast.loading('Creating experiment...', { id: 'launch-exp' });
      }
      
      await apiService.createExperiment(experimentData);
      
      toast.success('Experiment launched successfully!', { id: 'launch-exp' });
      loadExperiments();
    } catch (error) {
      toast.error('Failed to launch experiment', { id: 'launch-exp' });
      console.error('Launch error:', error);
    }
  };

  const handleClone = async (id: string) => {
    try {
      const originalArr: Experiment[] =
        Array.isArray(experimentsState)
          ? experimentsState
          : experimentsState && typeof experimentsState === "object" && !("length" in experimentsState)
            ? Object.values(experimentsState as Record<string, Experiment>)
            : [];
      const original = originalArr.find((exp) => exp.id === id);
      if (!original) return;

      toast.loading('Cloning experiment...', { id: 'clone' });
      await apiService.cloneExperiment(id, `${original.name} (Clone)`);
      toast.success('Experiment cloned!', { id: 'clone' });
      loadExperiments();
    } catch (error) {
      toast.error('Failed to clone experiment', { id: 'clone' });
    }
  };

  const handleStop = async (id: string) => {
    try {
      toast.loading('Stopping experiment...', { id: 'stop' });
      await apiService.stopExperiment(id);
      toast.success('Experiment stopped!', { id: 'stop' });
      loadExperiments();
    } catch (error) {
      toast.error('Failed to stop experiment', { id: 'stop' });
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this experiment?')) return;
    
    try {
      toast.loading('Deleting experiment...', { id: 'delete' });
      // API call would go here - using id parameter
      console.log('Deleting experiment:', id);
      toast.success('Experiment deleted!', { id: 'delete' });
      loadExperiments();
    } catch (error) {
      toast.error('Failed to delete experiment', { id: 'delete' });
    }
  };

  const handleView = (id: string) => {
    // Open ClearML experiment in new tab
    const clearmlUrl = `http://localhost:8080/projects/*/experiments/${id}`;
    window.open(clearmlUrl, '_blank');
  };

  console.debug("experiments type", {
    isArray: Array.isArray(experimentsState),
    type: typeof experimentsState,
    keys: experimentsState && typeof experimentsState === "object" ? Object.keys(experimentsState) : null,
    sample: Array.isArray(experimentsState) ? experimentsState[0] : null,
  });

  const experimentsArr: Experiment[] = experiments;

  const filteredExperiments = experimentsArr.filter((exp) => {
    if (filters.searchQuery && !(exp.name || '').toLowerCase().includes(filters.searchQuery.toLowerCase())) {
      return false;
    }
    if (filters.status.length > 0 && !filters.status.includes(exp.status)) {
      return false;
    }
    return true;
  });

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
            Experiments
          </h1>
          <p className="text-slate-400 mt-2">Manage and monitor your business agent simulations</p>
        </div>
        
        <div className="flex items-center space-x-4">
          <button
            onClick={() => setShowFilters(!showFilters)}
            className="flex items-center space-x-2 px-4 py-2 bg-slate-700/50 text-slate-300 rounded-lg hover:bg-slate-700 transition-colors"
          >
            <FunnelIcon className="h-4 w-4" />
            <span>Filters</span>
          </button>
          
          <motion.button
            onClick={() => setShowLaunchModal(true)}
            className="flex items-center space-x-2 px-6 py-3 bg-gradient-to-r from-violet-500 to-purple-500 text-white rounded-lg hover:from-violet-600 hover:to-purple-600 transition-all duration-200"
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            <RocketLaunchIcon className="h-4 w-4" />
            <span>Launch Experiment</span>
          </motion.button>
        </div>
      </motion.div>

      {/* Filters Panel */}
      <AnimatePresence>
        {showFilters && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="bg-slate-800/50 rounded-xl border border-slate-700/50 p-6 mb-6"
          >
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* Search */}
              <div>
                <label className="block text-slate-300 text-sm font-medium mb-2">Search</label>
                <input
                  type="text"
                  placeholder="Search experiments..."
                  value={filters.searchQuery}
                  onChange={(e) => setFilters({ searchQuery: e.target.value })}
                  className="w-full px-3 py-2 bg-slate-700/50 border border-slate-600/50 rounded-lg text-white placeholder-slate-400 focus:border-violet-500 focus:outline-none"
                />
              </div>
              
              {/* Status Filter */}
              <div>
                <label className="block text-slate-300 text-sm font-medium mb-2">Status</label>
                <select
                  multiple
                  value={filters.status}
                  onChange={(e) => setFilters({ status: Array.from(e.target.selectedOptions, option => option.value) })}
                  className="w-full px-3 py-2 bg-slate-700/50 border border-slate-600/50 rounded-lg text-white focus:border-violet-500 focus:outline-none"
                >
                  <option value="running">Running</option>
                  <option value="completed">Completed</option>
                  <option value="failed">Failed</option>
                  <option value="queued">Queued</option>
                </select>
              </div>
              
              {/* Project Filter */}
              <div>
                <label className="block text-slate-300 text-sm font-medium mb-2">Project</label>
                <input
                  type="text"
                  value={filters.project}
                  onChange={(e) => setFilters({ project: e.target.value })}
                  className="w-full px-3 py-2 bg-slate-700/50 border border-slate-600/50 rounded-lg text-white focus:border-violet-500 focus:outline-none"
                />
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Experiments Grid */}
      {loading.experiments ? (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-violet-400"></div>
        </div>
      ) : filteredExperiments.length > 0 ? (
        <motion.div
          className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
        >
          <AnimatePresence>
            {filteredExperiments.map((experiment) => (
              <ExperimentCard
                key={experiment.id}
                experiment={experiment}
                onView={handleView}
                onClone={handleClone}
                onStop={handleStop}
                onDelete={handleDelete}
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
          <BeakerIcon className="h-16 w-16 text-slate-600 mx-auto mb-6" />
          <h3 className="text-xl font-semibold text-slate-300 mb-4">No Experiments Found</h3>
          <p className="text-slate-400 mb-8 max-w-md mx-auto">
            Create your first experiment to start exploring business agent simulations and performance optimization.
          </p>
          
          <div className="space-y-4 max-w-md mx-auto">
            <button
              onClick={() => setShowLaunchModal(true)}
              className="w-full flex items-center justify-center space-x-2 px-6 py-3 bg-gradient-to-r from-violet-500 to-purple-500 text-white rounded-lg hover:from-violet-600 hover:to-purple-600 transition-all duration-200"
            >
              <RocketLaunchIcon className="h-5 w-5" />
              <span>Launch First Experiment</span>
            </button>
            
            <button
              onClick={() => {
                toast.promise(
                  // Call demo script
                  fetch('/api/v1/demo/populate', { method: 'POST' }),
                  {
                    loading: 'Creating demo experiments...',
                    success: 'Demo data created! Refresh to see experiments.',
                    error: 'Failed to create demo data'
                  }
                );
              }}
              className="w-full px-6 py-3 border border-slate-600/50 text-slate-300 rounded-lg hover:bg-slate-700/50 transition-colors"
            >
              Load Demo Data
            </button>
          </div>
          
          <div className="mt-8 p-6 bg-slate-800/30 rounded-lg border border-slate-700/30">
            <h4 className="text-white font-medium mb-3">Quick Start Tips:</h4>
            <ul className="text-slate-400 text-sm space-y-2 text-left">
              <li>• Use <code className="text-violet-400">fba-bench launch --game-mode</code> to create experiments</li>
              <li>• Clone successful experiments to build on proven strategies</li>
              <li>• Monitor real-time metrics to optimize performance</li>
              <li>• Compare multiple experiments to find winning patterns</li>
            </ul>
          </div>
        </motion.div>
      )}

      {/* Launch Modal */}
      <LaunchModal
        isOpen={showLaunchModal}
        onClose={() => setShowLaunchModal(false)}
        onLaunch={handleLaunchExperiment}
      />
    </div>
  );
};

export default Experiments;