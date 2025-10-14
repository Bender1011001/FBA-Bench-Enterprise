import React, { useState } from 'react';

const ONBOARDING_DISMISSED_KEY = 'fba.onboarding.dismissed';

interface OnboardingProps {}

const Onboarding: React.FC<OnboardingProps> = () => {
  const [dismissed, setDismissed] = useState(false);

  const handleRegister = () => {
    localStorage.setItem(ONBOARDING_DISMISSED_KEY, '1');
    window.location.hash = '#register';
  };

  const handleLogin = () => {
    localStorage.setItem(ONBOARDING_DISMISSED_KEY, '1');
    window.location.hash = '';
  };

  const handleDismiss = () => {
    setDismissed(true);
    localStorage.setItem(ONBOARDING_DISMISSED_KEY, '1');
    // Navigate to login by default
    window.location.hash = '';
  };

  if (dismissed) {
    return null; // Will be handled by App re-render
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8 text-center">
        <div>
          <h2 className="mt-6 text-3xl font-extrabold text-gray-900">
            Welcome to FBA-Bench
          </h2>
          <p className="mt-4 text-lg text-gray-600">
            The premier platform for simulating and benchmarking business AI agents. Get started by creating an account or logging in to access powerful simulation tools.
          </p>
        </div>
        <div className="space-y-4">
          <button
            onClick={handleRegister}
            className="group relative w-full flex justify-center py-3 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
          >
            Get Started — Register
          </button>
          <button
            onClick={handleLogin}
            className="group relative w-full flex justify-center py-3 px-4 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
          >
            I already have an account — Login
          </button>
        </div>
        <div className="pt-5">
          <button
            onClick={handleDismiss}
            className="text-sm text-gray-500 hover:text-gray-700"
          >
            Don't show again
          </button>
        </div>
      </div>
    </div>
  );
};

export default Onboarding;