import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import ControlCenter from './ControlCenter';

vi.mock('zustand', () => ({
  create: vi.fn(() => ({
    getState: vi.fn(),
    setState: vi.fn(),
    subscribe: vi.fn(),
  })),
}));

import * as stackService from 'services/stack';
import * as simulationService from 'services/simulation';

vi.mock('services/stack');
vi.mock('services/simulation');
vi.mock('services/settings');

import * as settingsService from 'services/settings';

const mockGetClearMLStackStatus = vi.mocked(stackService.getClearMLStackStatus);
const mockStartClearMLStack = vi.mocked(stackService.startClearMLStack);
const mockGetRuntimeConfig = vi.mocked(settingsService.getRuntimeConfig);
const mockGetSettings = vi.mocked(settingsService.getSettings);
const mockPauseSimulation = vi.mocked(simulationService.pauseSimulation);
const mockStopSimulation = vi.mocked(simulationService.stopSimulation);
const mockSetSimulationSpeed = vi.mocked(simulationService.setSimulationSpeed);
const mockGetSimulationSnapshot = vi.mocked(simulationService.getSimulationSnapshot);


// Mock other dependencies if needed

describe('ControlCenter', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGetClearMLStackStatus.mockResolvedValue({ ports: { web: true, api: true, file: true } });
    mockGetSimulationSnapshot.mockResolvedValue({ status: 'running', day: 1, tick: 10 });
    mockGetRuntimeConfig.mockResolvedValue({ key: 'value' });
    mockGetSettings.mockResolvedValue({ theme: 'dark' });
  });

  it('renders without crashing', () => {
    render(
      <MemoryRouter initialEntries={['/control']}>
        <ControlCenter />
      </MemoryRouter>
    );
  });

  it('renders section titles', () => {
    render(
      <MemoryRouter initialEntries={['/control']}>
        <ControlCenter />
      </MemoryRouter>
    );
    expect(screen.getByText('ClearML Stack')).toBeInTheDocument();
    expect(screen.getByText('Orchestrator')).toBeInTheDocument();
    expect(screen.getByText('Settings')).toBeInTheDocument();
  });

  it('renders compose path input and stack buttons', () => {
    render(
      <MemoryRouter initialEntries={['/control']}>
        <ControlCenter />
      </MemoryRouter>
    );
    const input = screen.getByRole('textbox');
    expect(input).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /start stack/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /stop stack/i })).toBeInTheDocument();
  });

  it('renders orchestrator buttons and speed input', () => {
    render(
      <MemoryRouter initialEntries={['/control']}>
        <ControlCenter />
      </MemoryRouter>
    );
    expect(screen.getByRole('button', { name: /start/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /pause/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /resume/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /stop/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /set speed/i })).toBeInTheDocument();
    const speedInput = screen.getByRole('spinbutton');
    expect(speedInput).toBeInTheDocument();
  });

  it('renders JSON blocks', () => {
    render(
      <MemoryRouter initialEntries={['/control']}>
        <ControlCenter />
      </MemoryRouter>
    );
    expect(screen.getByText('Status JSON')).toBeInTheDocument();
    expect(screen.getByText('Snapshot JSON')).toBeInTheDocument();
  });

  it('calls startClearMLStack when start stack button is clicked', async () => {
    mockStartClearMLStack.mockResolvedValue({ success: true });

    render(
      <MemoryRouter initialEntries={['/control']}>
        <ControlCenter />
      </MemoryRouter>
    );

    const startButton = screen.getByRole('button', { name: /start stack/i });
    fireEvent.click(startButton);

    await waitFor(() => expect(mockStartClearMLStack).toHaveBeenCalled());
  });

  it('calls pauseSimulation when pause button is clicked', async () => {
    mockPauseSimulation.mockResolvedValue({ success: true });

    render(
      <MemoryRouter initialEntries={['/control']}>
        <ControlCenter />
      </MemoryRouter>
    );

    const pauseButton = screen.getByRole('button', { name: /pause/i });
    fireEvent.click(pauseButton);

    await waitFor(() => expect(mockPauseSimulation).toHaveBeenCalled());
  });

  it('calls stopSimulation when stop button is clicked', async () => {
    mockStopSimulation.mockResolvedValue({ success: true });

    render(
      <MemoryRouter initialEntries={['/control']}>
        <ControlCenter />
      </MemoryRouter>
    );

    const stopButton = screen.getByRole('button', { name: /stop/i });
    fireEvent.click(stopButton);

    await waitFor(() => expect(mockStopSimulation).toHaveBeenCalled());
  });

  it('calls setSimulationSpeed when set speed button is clicked after input change', async () => {
    mockSetSimulationSpeed.mockResolvedValue({ success: true });

    render(
      <MemoryRouter initialEntries={['/control']}>
        <ControlCenter />
      </MemoryRouter>
    );

    const speedInput = screen.getByRole('spinbutton');
    fireEvent.change(speedInput, { target: { value: '2' } });

    const setSpeedButton = screen.getByRole('button', { name: /set speed/i });
    fireEvent.click(setSpeedButton);

    await waitFor(() => expect(mockSetSimulationSpeed).toHaveBeenCalledWith(2));
  });

  it('renders status indicators for stack', async () => {
    render(
      <MemoryRouter initialEntries={['/control']}>
        <ControlCenter />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Open')).toBeInTheDocument();
      const webIndicator = screen.getAllByText('Open')[0].closest('.status-indicator');
      expect(webIndicator).toHaveClass('status-ok');
    });
  });

  it('shows error alert when service call fails', async () => {
    mockGetClearMLStackStatus.mockRejectedValue(new Error('Test error'));

    render(
      <MemoryRouter initialEntries={['/control']}>
        <ControlCenter />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Failed to fetch stack status')).toBeInTheDocument();
    });
  });

  it('renders textarea for runtime config and settings', () => {
    render(
      <MemoryRouter initialEntries={['/control']}>
        <ControlCenter />
      </MemoryRouter>
    );

    const textareas = screen.getAllByRole('textbox', { name: '' });
    expect(textareas.length).toBeGreaterThan(0); // At least the compose input, but textareas for JSON
    expect(screen.getByText('Runtime Config')).toBeInTheDocument();
    expect(screen.getByText('UI Settings')).toBeInTheDocument();
  });
});