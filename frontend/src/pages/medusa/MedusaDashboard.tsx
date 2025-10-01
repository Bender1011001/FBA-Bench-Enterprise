import React, { useState, useEffect, useCallback } from 'react';
import { getMedusaStatus, startMedusaTrainer, stopMedusaTrainer, getMedusaLogs, getMedusaAnalysis } from '../../api/medusa';
import toast from 'react-hot-toast';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

// --- Type Definitions ---
interface MedusaStatus {
  status: 'running' | 'stopped';
  pid: number | null;
}

interface MedusaAnalysisReport {
  evolutionary_summary?: {
    total_generations: number;
    elite_agents: number;
    candidates_tested: number;
    promotion_rate: number;
    best_performance: number;
  };
  generation_analysis?: {
    generation: number;
    elite_performance?: number;
    candidate_performance?: number;
  }[];
  // Add other fields from the report as needed
}

// --- Helper Components ---
const StatCard: React.FC<{ title: string; value: string | number }> = ({ title, value }) => (
  <div className="bg-gray-800 p-4 rounded-lg shadow-md text-center">
    <h3 className="text-sm text-gray-400 font-medium">{title}</h3>
    <p className="text-2xl font-bold text-white">{value}</p>
  </div>
);

const StatusIndicator: React.FC<{ status: 'running' | 'stopped' }> = ({ status }) => (
  <div className="flex items-center space-x-2">
    <span className={`h-3 w-3 rounded-full ${status === 'running' ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`}></span>
    <span className="text-white font-medium capitalize">{status}</span>
  </div>
);


const MedusaDashboard: React.FC = () => {
  const [status, setStatus] = useState<MedusaStatus>({ status: 'stopped', pid: null });
  const [logs, setLogs] = useState<string>('Awaiting trainer start...');
  const [analysis, setAnalysis] = useState<MedusaAnalysisReport | null>(null);
  const [isLoading, setIsLoading] = useState({
    status: true,
    logs: true,
    analysis: true,
    action: false,
  });

  const handleError = (message: string, error: unknown) => {
    console.error(message, error);
    toast.error(message);
  };

  // --- API Callbacks ---
  const fetchStatus = useCallback(async () => {
    try {
      const statusData = await getMedusaStatus();
      setStatus(statusData);
    } catch (error) {
      handleError('Failed to fetch Medusa status.', error);
    } finally {
      setIsLoading(prev => ({ ...prev, status: false }));
    }
  }, []);

  const fetchLogs = useCallback(async () => {
    try {
      const logData = await getMedusaLogs();
      setLogs(logData || 'Log file is empty.');
    } catch (error) {
      handleError('Failed to fetch Medusa logs.', error);
    } finally {
      setIsLoading(prev => ({ ...prev, logs: false }));
    }
  }, []);

  const fetchAnalysis = useCallback(async () => {
    setIsLoading(prev => ({ ...prev, analysis: true }));
    try {
      const analysisData = await getMedusaAnalysis();
      setAnalysis(analysisData);
    } catch (error) {
      handleError('Failed to fetch Medusa analysis report.', error);
      setAnalysis(null); // Clear old data on error
    } finally {
      setIsLoading(prev => ({ ...prev, analysis: false }));
    }
  }, []);
  
  // --- Control Actions ---
  const handleStart = async () => {
    if (status.status === 'running') {
        toast.error("Trainer is already running.");
        return;
    }
    setIsLoading(prev => ({ ...prev, action: true }));
    try {
      const response = await startMedusaTrainer();
      toast.success(response.message);
      await fetchStatus(); // Immediately update status
    } catch (error) {
      handleError('Failed to start Medusa trainer.', error);
    } finally {
      setIsLoading(prev => ({ ...prev, action: false }));
    }
  };

  const handleStop = async () => {
     if (status.status !== 'running') {
        toast.error("Trainer is not running.");
        return;
    }
    setIsLoading(prev => ({ ...prev, action: true }));
    try {
      const response = await stopMedusaTrainer();
      toast.success(response.message);
      await fetchStatus(); // Immediately update status
    } catch (error) {
      handleError('Failed to stop Medusa trainer.', error);
    } finally {
      setIsLoading(prev => ({ ...prev, action: false }));
    }
  };


  // --- Effects for Polling ---
  useEffect(() => {
    // Initial fetch
    fetchStatus();
    fetchLogs();
    fetchAnalysis();

    // Set up polling
    const statusInterval = setInterval(fetchStatus, 5000); // every 5s
    const logsInterval = setInterval(fetchLogs, 10000); // every 10s
    
    return () => {
      clearInterval(statusInterval);
      clearInterval(logsInterval);
    };
  }, [fetchStatus, fetchLogs, fetchAnalysis]);

  // --- Render Logic ---
  const summary = analysis?.evolutionary_summary;
  const chartData = analysis?.generation_analysis?.map(gen => ({
      name: `Gen ${gen.generation}`,
      elite: gen.elite_performance,
      candidate: gen.candidate_performance,
  }));

  return (
    <div className="p-6 bg-gray-900 min-h-screen text-gray-200">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold text-white">Project Medusa Dashboard</h1>
        <div className="flex items-center space-x-4">
          <StatusIndicator status={status.status} />
          <button onClick={handleStart} disabled={isLoading.action || status.status === 'running'} className="bg-green-600 hover:bg-green-700 disabled:bg-gray-500 text-white font-bold py-2 px-4 rounded-lg transition">
            {isLoading.action ? 'Starting...' : 'Start Evolution'}
          </button>
          <button onClick={handleStop} disabled={isLoading.action || status.status !== 'running'} className="bg-red-600 hover:bg-red-700 disabled:bg-gray-500 text-white font-bold py-2 px-4 rounded-lg transition">
            {isLoading.action ? 'Stopping...' : 'Stop Evolution'}
          </button>
           <button onClick={fetchAnalysis} disabled={isLoading.analysis} className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-500 text-white font-bold py-2 px-4 rounded-lg transition">
            {isLoading.analysis ? 'Refreshing...' : 'Refresh Analysis'}
          </button>
        </div>
      </div>

      {/* --- Key Metrics --- */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
        <StatCard title="Total Generations" value={summary?.total_generations ?? 'N/A'} />
        <StatCard title="Best Performance" value={summary ? `$${summary.best_performance.toFixed(2)}` : 'N/A'} />
        <StatCard title="Elite Agents" value={summary?.elite_agents ?? 'N/A'} />
        <StatCard title="Candidates Tested" value={summary?.candidates_tested ?? 'N/A'} />
        <StatCard title="Promotion Rate" value={summary ? `${(summary.promotion_rate * 100).toFixed(1)}%` : 'N/A'} />
      </div>

      {/* --- Main Content Area --- */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* --- Performance Chart --- */}
        <div className="lg:col-span-2 bg-gray-800 p-4 rounded-lg shadow-lg">
          <h2 className="text-xl font-semibold mb-4 text-white">Performance Evolution</h2>
          {isLoading.analysis ? (
             <div className="flex items-center justify-center h-80 text-white">Loading chart data...</div>
          ) : (
            <ResponsiveContainer width="100%" height={400}>
              <LineChart data={chartData} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#4a5568" />
                <XAxis dataKey="name" stroke="#a0aec0" />
                <YAxis stroke="#a0aec0" />
                <Tooltip contentStyle={{ backgroundColor: '#2d3748', border: 'none' }} />
                <Legend />
                <Line type="monotone" dataKey="elite" stroke="#48bb78" strokeWidth={2} name="Elite Agent" />
                <Line type="monotone" dataKey="candidate" stroke="#f6ad55" strokeWidth={2} name="Candidate Agent" />
              </LineChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* --- Live Logs --- */}
        <div className="bg-gray-800 rounded-lg p-4 overflow-hidden h-[448px] flex flex-col">
            <h2 className="text-xl font-semibold mb-4 text-white">Live Trainer Logs</h2>
            {isLoading.logs ? (
                 <div className="flex items-center justify-center flex-grow text-white">Loading logs...</div>
            ) : (
                <pre className="text-xs font-mono text-gray-300 flex-grow overflow-y-auto whitespace-pre-wrap p-2 bg-gray-900 rounded">
                    {logs}
                </pre>
            )}
        </div>
      </div>
    </div>
  );
};

export default MedusaDashboard;