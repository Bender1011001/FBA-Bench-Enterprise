/* 
  Note: After updating the test toolchain, run `cd frontend && npm install` to fetch new devDependencies 
  for VS Code to resolve types properly.
*/

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import userEvent from '@testing-library/user-event';
import MedusaDashboard from '../../frontend/src/pages/medusa/MedusaDashboard';
import * as apiService from '../../frontend/src/api/medusa';

// Mock the apiService functions
vi.mock('../../frontend/src/api/medusa', () => ({
  getMedusaStatus: vi.fn(),
  startMedusaTrainer: vi.fn(),
  stopMedusaTrainer: vi.fn(),
  getMedusaLogs: vi.fn(),
  getMedusaAnalysis: vi.fn(),
});

const mockGetStatus = vi.mocked(apiService.getMedusaStatus);
const mockStartTrainer = vi.mocked(apiService.startMedusaTrainer);
const mockStopTrainer = vi.mocked(apiService.stopMedusaTrainer);
const mockGetLogs = vi.mocked(apiService.getMedusaLogs);
const mockGetAnalysis = vi.mocked(apiService.getMedusaAnalysis);

describe('MedusaDashboard Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders the dashboard and displays initial state', async () => {
    mockGetStatus.mockResolvedValue({ status: 'stopped', pid: null });
    mockGetLogs.mockResolvedValue('Initial log message');
    mockGetAnalysis.mockResolvedValue(null);

    render(
      <BrowserRouter>
        <MedusaDashboard />
      </BrowserRouter>
    );

    expect(screen.getByText('Project Medusa Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Start Evolution')).toBeInTheDocument();
    expect(screen.getByText('Stop Evolution')).toBeInTheDocument();
    expect(screen.getByText('Refresh Analysis')).toBeInTheDocument();
    expect(screen.getByText('Awaiting trainer start...')).toBeInTheDocument();
  });

  it('handles start trainer action successfully', async () => {
    const user = userEvent.setup();
    mockGetStatus.mockResolvedValue({ status: 'stopped', pid: null });
    mockGetLogs.mockResolvedValue('Logs after start');
    mockGetAnalysis.mockResolvedValue(null);
    mockStartTrainer.mockResolvedValue({ status: 'started', message: 'Started with PID 1234' });

    render(
      <BrowserRouter>
        <MedusaDashboard />
      </BrowserRouter>
    );

    const startButton = screen.getByText('Start Evolution');
    await user.click(startButton);

    await waitFor(() => {
      expect(mockStartTrainer).toHaveBeenCalledTimes(1);
    });
  });

  it('handles stop trainer action successfully', async () => {
    const user = userEvent.setup();
    mockGetStatus.mockResolvedValue({ status: 'running', pid: 1234 });
    mockGetLogs.mockResolvedValue('Logs after stop');
    mockGetAnalysis.mockResolvedValue(null);
    mockStopTrainer.mockResolvedValue({ status: 'stopped', message: 'Stopped PID 1234' });

    render(
      <BrowserRouter>
        <MedusaDashboard />
      </BrowserRouter>
    );

    const stopButton = screen.getByText('Stop Evolution');
    await user.click(stopButton);

    await waitFor(() => {
      expect(mockStopTrainer).toHaveBeenCalledTimes(1);
    });
  });

  it('polls status and updates the indicator', async () => {
    const user = userEvent.setup();
    mockGetStatus
      .mockResolvedValueOnce({ status: 'stopped', pid: null })
      .mockResolvedValueOnce({ status: 'running', pid: 1234 });
    mockGetLogs.mockResolvedValue('Polling logs');
    mockGetAnalysis.mockResolvedValue(null);

    render(
      <BrowserRouter>
        <MedusaDashboard />
      </BrowserRouter>
    );

    // Initial render shows stopped
    expect(screen.getByText('stopped')).toBeInTheDocument();

    // Simulate polling update to running
    await waitFor(() => {
      expect(screen.getByText('running')).toBeInTheDocument();
    }, { timeout: 1000 });
  });

  it('polls logs and updates the log viewer', async () => {
    mockGetStatus.mockResolvedValue({ status: 'running', pid: 1234 });
    mockGetLogs
      .mockResolvedValueOnce('Initial logs')
      .mockResolvedValueOnce('Updated logs after poll');
    mockGetAnalysis.mockResolvedValue(null);

    render(
      <BrowserRouter>
        <MedusaDashboard />
      </BrowserRouter>
    );

    // Initial logs
    expect(screen.getByText('Initial logs')).toBeInTheDocument();

    // Simulate log polling update
    await waitFor(() => {
      expect(screen.getByText('Updated logs after poll')).toBeInTheDocument();
    }, { timeout: 1000 });
  });

  it('polls analysis and renders the chart', async () => {
    const analysisData = {
      evolutionary_summary: {
        total_generations: 5,
        elite_agents: 2,
        candidates_tested: 10,
        promotion_rate: 0.4,
        best_performance: 85.5,
      },
      generation_analysis: [
        { generation: 1, elite_performance: 70, candidate_performance: 65 },
        { generation: 2, elite_performance: 75, candidate_performance: 68 },
        { generation: 3, elite_performance: 80, candidate_performance: 72 },
        { generation: 4, elite_performance: 82, candidate_performance: 78 },
        { generation: 5, elite_performance: 85.5, candidate_performance: 80 },
      ],
    };

    mockGetStatus.mockResolvedValue({ status: 'stopped', pid: null });
    mockGetLogs.mockResolvedValue('Analysis logs');
    mockGetAnalysis.mockResolvedValue(analysisData);

    render(
      <BrowserRouter>
        <MedusaDashboard />
      </BrowserRouter>
    );

    // Initial loading state
    expect(screen.getByText('Loading chart data...')).toBeInTheDocument();

    // Simulate analysis polling
    await waitFor(() => {
      expect(screen.getByText('Total Generations')).toBeInTheDocument();
      expect(screen.getByText('5')).toBeInTheDocument();
      expect(screen.getByText('Best Performance')).toBeInTheDocument();
      expect(screen.getByText('85.5')).toBeInTheDocument();
    }, { timeout: 1000 });
  });

  it('handles errors gracefully with toasts', async () => {
    mockGetStatus.mockRejectedValue(new Error('Network error'));
    mockGetLogs.mockRejectedValue(new Error('Log fetch failed'));
    mockGetAnalysis.mockRejectedValue(new Error('Analysis failed'));

    render(
      <BrowserRouter>
        <MedusaDashboard />
      </BrowserRouter>
    );

    // Errors should be handled without crashing
    await waitFor(() => {
      expect(screen.getByText('Project Medusa Dashboard')).toBeInTheDocument();
    });
  });
});