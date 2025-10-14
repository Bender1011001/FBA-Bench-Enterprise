import React from 'react';
import { XMarkIcon } from '@heroicons/react/24/outline';

interface HelpOverlayProps {
  page: 'login' | 'register' | 'account' | 'billing';
  open: boolean;
  onClose: () => void;
}

const HelpOverlay: React.FC<HelpOverlayProps> = ({ page, open, onClose }) => {
  if (!open) return null;

  const helpContent = {
    login: {
      title: 'Login Help',
      content: (
        <div>
          <p className="mb-4">
            Use your registered email and password to sign in. If you encounter issues, ensure your credentials are correct and check the{' '}
            <a
              href="https://github.com/fba-bench-enterprise/blob/main/README.md#authentication"
              target="_blank"
              rel="noopener noreferrer"
              className="text-indigo-600 hover:text-indigo-800 underline"
            >
              Auth API documentation
            </a>{' '}
            for troubleshooting.
          </p>
          <p className="mb-4">
            Common issues: Invalid credentials (401), network errors, or server not running.
          </p>
        </div>
      ),
    },
    register: {
      title: 'Register Help',
      content: (
        <div>
          <p className="mb-4">
            Create a new account with a valid email and password (minimum 8 characters). After registration, you can log in immediately.
          </p>
          <p className="mb-4">
            Password policy: At least 8 characters. See the{' '}
            <a
              href="https://github.com/fba-bench-enterprise/blob/main/README.md#authentication"
              target="_blank"
              rel="noopener noreferrer"
              className="text-indigo-600 hover:text-indigo-800 underline"
            >
              Auth API docs
            </a>{' '}
            for details.
          </p>
          <p>
            If email is already taken, try a different one or log in if you have an account.
          </p>
        </div>
      ),
    },
    account: {
      title: 'Account Help',
      content: (
        <div>
          <p className="mb-4">
            View your profile details fetched via the{' '}
            <a
              href="https://github.com/fba-bench-enterprise/blob/main/README.md#get-me-profile"
              target="_blank"
              rel="noopener noreferrer"
              className="text-indigo-600 hover:text-indigo-800 underline"
            >
              GET /me endpoint
            </a>
            . This uses your JWT access token for authentication.
          </p>
          <p className="mb-4">
            JWT notes: Tokens expire after 24 hours; log in again if needed. No refresh tokens implemented yet.
          </p>
          <p>
            Sign out clears the token from localStorage.
          </p>
        </div>
      ),
    },
    billing: {
      title: 'Billing Help',
      content: (
        <div>
          <p className="mb-4">
            Manage subscriptions via Stripe integration. Use the Subscribe button to start a checkout session or Manage Billing for the customer portal.
          </p>
          <p className="mb-4">
            See the{' '}
            <a
              href="https://github.com/fba-bench-enterprise/blob/main/README.md#stripe-integration"
              target="_blank"
              rel="noopener noreferrer"
              className="text-indigo-600 hover:text-indigo-800 underline"
            >
              Stripe sections
            </a>{' '}
            for Checkout, Webhooks, and Portal setup. Ensure STRIPE_DEFAULT_PRICE_ID is configured on the backend.
          </p>
          <p>
            Webhooks handle subscription events automatically.
          </p>
        </div>
      ),
    },
  };

  const currentHelp = helpContent[page];

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg max-w-md w-full max-h-[80vh] overflow-y-auto">
        <div className="p-6">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-medium text-gray-900">{currentHelp.title}</h3>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600"
            >
              <XMarkIcon className="h-6 w-6" />
            </button>
          </div>
          <div className="prose prose-sm text-gray-700">
            {currentHelp.content}
          </div>
        </div>
      </div>
    </div>
  );
};

export default HelpOverlay;