import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import LoadingScreen from './LoadingScreen';

describe('LoadingScreen', () => {
  it('renders without crashing', () => {
    render(<LoadingScreen />);
  });

  it('renders the gradient background container', () => {
    render(<LoadingScreen />);
    const container = screen.getByTestId('loading-container'); // Add data-testid="loading-container" to the div in LoadingScreen if needed
    expect(container).toHaveClass('min-h-screen', 'bg-gradient-to-br', 'from-slate-900', 'via-purple-900', 'to-slate-900');
  });

  it('renders the title', () => {
    render(<LoadingScreen />);
    const title = screen.getByText('FBA-Bench Dashboard');
    expect(title).toBeInTheDocument();
    expect(title).toHaveClass('text-2xl', 'font-bold', 'bg-gradient-to-r', 'from-violet-400', 'to-purple-400', 'bg-clip-text', 'text-transparent');
  });

  it('renders the loading message', () => {
    render(<LoadingScreen />);
    const message = screen.getByText('Initializing business simulation platform...');
    expect(message).toBeInTheDocument();
    expect(message).toHaveClass('text-slate-300');
  });

  it('renders three progress dots', () => {
    render(<LoadingScreen />);
    const dots = screen.getAllByTestId('progress-dot'); // Add data-testid="progress-dot" to each motion.div in LoadingScreen
    expect(dots).toHaveLength(3);
    dots.forEach(dot => {
      expect(dot).toHaveClass('w-3', 'h-3', 'bg-violet-400', 'rounded-full');
    });
  });

  it('renders the logo container', () => {
    render(<LoadingScreen />);
    const logo = screen.getByTestId('logo-container'); // Add data-testid="logo-container" to the motion.div with logo
    expect(logo).toBeInTheDocument();
  });
});