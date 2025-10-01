/* Centralized guided tour steps extracted from App.tsx
   Note: Using .tsx to allow JSX in step content; imported later by App.tsx
*/
import React, { type ReactNode } from 'react';

export type TourStep = {
  id: number;
  title: string;
  description: string;
  target: string;
  position: 'bottom' | 'right' | 'left' | 'top';
  content: ReactNode;
};

export const tourSteps: TourStep[] = [
  {
    id: 0,
    title: 'Welcome to FBA-Bench',
    description: 'This guided tour will help you get started with the platform.',
    target: '.logo-brand',
    position: 'bottom',
    content: (
      <div>
        <p>You're now using the FBA-Bench platform for business agent simulation.</p>
        <p className="mt-2">Let's explore the main features.</p>
      </div>
    )
  },
  {
    id: 1,
    title: 'Dashboard Overview',
    description: 'The dashboard shows key metrics and recent activity.',
    target: '.metric-card',
    position: 'right',
    content: (
      <div>
        <p>Monitor your experiments with real-time metrics and performance indicators.</p>
        <p className="mt-2 text-sm text-gray-600">Click "Start New Experiment" to begin your first simulation.</p>
      </div>
    )
  },
  {
    id: 2,
    title: 'Experiments Management',
    description: 'Manage all your business simulations from the Experiments page.',
    target: '.nav-experiments',
    position: 'bottom',
    content: (
      <div>
        <p>Create, monitor, and analyze your agent experiments.</p>
        <p className="mt-2 text-sm text-gray-600">Track performance, view results, and compare different strategies.</p>
      </div>
    )
  },
  {
    id: 3,
    title: 'Leaderboard',
    description: 'See how your agents perform compared to others.',
    target: '.nav-leaderboard',
    position: 'bottom',
    content: (
      <div>
        <p>View the top performing agents and benchmark your results.</p>
        <p className="mt-2 text-sm text-gray-600">Use this to identify the best strategies and areas for improvement.</p>
      </div>
    )
  },
  {
    id: 4,
    title: 'Settings & Configuration',
    description: 'Customize your platform settings and integrations.',
    target: '.nav-settings',
    position: 'bottom',
    content: (
      <div>
        <p>Configure ClearML integration, API settings, and user preferences.</p>
        <p className="mt-2 text-sm text-gray-600">You can always return to this tour from the help menu.</p>
      </div>
    )
  }
];