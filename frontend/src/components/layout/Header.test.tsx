import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { Header } from './Header';

describe('Header', () => {
  const mockOnNavigate = vi.fn();

  it('renders the brand name', () => {
    render(<Header current="home" onNavigate={mockOnNavigate} />);
    const brand = screen.getByText('FBA-Bench');
    expect(brand).toBeInTheDocument();
    expect(brand).toHaveClass('text-xl', 'font-semibold', 'text-gray-900');
  });

  it('renders the badge', () => {
    render(<Header current="home" onNavigate={mockOnNavigate} />);
    const badge = screen.getByText('Dashboard');
    expect(badge).toBeInTheDocument();
    expect(badge).toHaveClass('badge', 'badge-gray');
  });

  it('renders Home tab as active when current is home', () => {
    render(<Header current="home" onNavigate={mockOnNavigate} />);
    const homeTab = screen.getByRole('button', { name: 'Home' });
    expect(homeTab).toHaveClass('tab-button-active');
    expect(homeTab).toHaveAttribute('aria-current', 'page');
  });

  it('renders Control Center tab as inactive when current is home', () => {
    render(<Header current="home" onNavigate={mockOnNavigate} />);
    const controlTab = screen.getByRole('button', { name: 'Control Center' });
    expect(controlTab).toHaveClass('tab-button-inactive');
    expect(controlTab).not.toHaveAttribute('aria-current', 'page');
  });

  it('calls onNavigate when Home tab is clicked', () => {
    render(<Header current="home" onNavigate={mockOnNavigate} />);
    const homeTab = screen.getByRole('button', { name: 'Home' });
    fireEvent.click(homeTab);
    expect(mockOnNavigate).toHaveBeenCalledWith('home');
  });

  it('calls onNavigate when Control Center tab is clicked', () => {
    render(<Header current="home" onNavigate={mockOnNavigate} />);
    const controlTab = screen.getByRole('button', { name: 'Control Center' });
    fireEvent.click(controlTab);
    expect(mockOnNavigate).toHaveBeenCalledWith('control');
  });

  it('renders Control Center tab as active when current is control', () => {
    render(<Header current="control" onNavigate={mockOnNavigate} />);
    const controlTab = screen.getByRole('button', { name: 'Control Center' });
    expect(controlTab).toHaveClass('tab-button-active');
    expect(controlTab).toHaveAttribute('aria-current', 'page');
  });

  it('renders Home tab as inactive when current is control', () => {
    render(<Header current="control" onNavigate={mockOnNavigate} />);
    const homeTab = screen.getByRole('button', { name: 'Home' });
    expect(homeTab).toHaveClass('tab-button-inactive');
    expect(homeTab).not.toHaveAttribute('aria-current', 'page');
  });
});