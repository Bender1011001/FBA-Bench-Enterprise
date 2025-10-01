import React from 'react';

export type AppScreen = 'home' | 'control';

interface HeaderProps {
  current: AppScreen;
  onNavigate: (screen: AppScreen) => void;
}

export const Header: React.FC<HeaderProps> = ({ current, onNavigate }) => {
  return (
    <header className="bg-white border-b border-gray-200">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="py-4 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <span className="text-xl font-semibold text-gray-900">FBA-Bench</span>
            <span className="badge badge-gray">Dashboard</span>
          </div>
          <nav className="tab-list">
            <button
              className={current === 'home' ? 'tab-button-active' : 'tab-button-inactive'}
              onClick={() => onNavigate('home')}
              aria-current={current === 'home' ? 'page' : undefined}
            >
              Home
            </button>
            <button
              className={current === 'control' ? 'tab-button-active' : 'tab-button-inactive'}
              onClick={() => onNavigate('control')}
              aria-current={current === 'control' ? 'page' : undefined}
            >
              Control Center
            </button>
          </nav>
        </div>
      </div>
    </header>
  );
};

export default Header;
