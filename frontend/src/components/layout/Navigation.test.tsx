import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import Navigation from './Navigation';

describe('Navigation', () => {
  it('renders the logo and brand', () => {
    render(
      <MemoryRouter initialEntries={['/dashboard']}>
        <Navigation apiConnected={true} clearmlConnected={true} />
      </MemoryRouter>
    );
    const brand = screen.getByText('FBA-Bench');
    expect(brand).toBeInTheDocument();
    expect(brand).toHaveClass('text-xl', 'font-bold', 'text-gray-900');
    const subtitle = screen.getByText('Business Agent Simulation Platform');
    expect(subtitle).toBeInTheDocument();
    expect(subtitle).toHaveClass('text-xs', 'text-gray-500');
  });

  it('renders navigation links', () => {
    render(
      <MemoryRouter initialEntries={['/dashboard']}>
        <Navigation apiConnected={true} clearmlConnected={true} />
      </MemoryRouter>
    );
    const links = [
      { path: '/dashboard', label: 'Dashboard' },
      { path: '/experiments', label: 'Experiments' },
      { path: '/leaderboard', label: 'Leaderboard' },
      { path: '/settings', label: 'Settings' },
    ];
    links.forEach(({ label }) => {
      const link = screen.getByText(label);
      expect(link).toBeInTheDocument();
    });
  });

  it('highlights Dashboard as active when on /dashboard', () => {
    render(
      <MemoryRouter initialEntries={['/dashboard']}>
        <Navigation apiConnected={true} clearmlConnected={true} />
      </MemoryRouter>
    );
    const dashboardLink = screen.getByRole('link', { name: 'Dashboard' });
    expect(dashboardLink).toHaveClass('text-blue-600', 'bg-blue-50', 'border-b-2', 'border-blue-600');
  });

  it('highlights Experiments as active when on /experiments', () => {
    render(
      <MemoryRouter initialEntries={['/experiments']}>
        <Navigation apiConnected={true} clearmlConnected={true} />
      </MemoryRouter>
    );
    const experimentsLink = screen.getByRole('link', { name: 'Experiments' });
    expect(experimentsLink).toHaveClass('text-blue-600', 'bg-blue-50', 'border-b-2', 'border-blue-600');
  });

  it('shows green icon for connected API', () => {
    render(
      <MemoryRouter initialEntries={['/dashboard']}>
        <Navigation apiConnected={true} clearmlConnected={false} />
      </MemoryRouter>
    );
    const apiStatus = screen.getByText('API');
    const apiIcon = apiStatus.parentElement!.querySelector('svg');
    expect(apiIcon).toHaveClass('text-green-500');
  });

  it('shows red icon for disconnected API', () => {
    render(
      <MemoryRouter initialEntries={['/dashboard']}>
        <Navigation apiConnected={false} clearmlConnected={true} />
      </MemoryRouter>
    );
    const apiStatus = screen.getByText('API');
    const apiIcon = apiStatus.parentElement!.querySelector('svg');
    expect(apiIcon).toHaveClass('text-red-500');
  });

  it('shows green icon for connected ClearML', () => {
    render(
      <MemoryRouter initialEntries={['/dashboard']}>
        <Navigation apiConnected={false} clearmlConnected={true} />
      </MemoryRouter>
    );
    const clearmlStatus = screen.getByText('ClearML');
    const clearmlIcon = clearmlStatus.parentElement!.querySelector('svg');
    expect(clearmlIcon).toHaveClass('text-green-500');
  });

  it('shows orange icon for disconnected ClearML', () => {
    render(
      <MemoryRouter initialEntries={['/dashboard']}>
        <Navigation apiConnected={true} clearmlConnected={false} />
      </MemoryRouter>
    );
    const clearmlStatus = screen.getByText('ClearML');
    const clearmlIcon = clearmlStatus.parentElement!.querySelector('svg');
    expect(clearmlIcon).toHaveClass('text-orange-500');
  });

  it('renders icons for each navigation link', () => {
    render(
      <MemoryRouter initialEntries={['/dashboard']}>
        <Navigation apiConnected={true} clearmlConnected={true} />
      </MemoryRouter>
    );
    const navIcons = screen.getAllByTestId('nav-icon');
    expect(navIcons).toHaveLength(4);
  });
});