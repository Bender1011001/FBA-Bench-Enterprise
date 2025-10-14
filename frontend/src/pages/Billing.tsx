import React, { useState, useEffect } from 'react';
import { createCheckoutSession, createPortalSession } from '../api/billing';
import { getToken } from '../auth/tokenStorage';

const Billing: React.FC = () => {
  const [subscribeLoading, setSubscribeLoading] = useState(false);
  const [portalLoading, setPortalLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [priceId, setPriceId] = useState('');

  useEffect(() => {
    if (!getToken()) {
      // Redirect to login by clearing hash
      window.location.hash = '';
      return;
    }
  }, []);

  if (!getToken()) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <p>Redirecting to login...</p>
        </div>
      </div>
    );
  }

  const handleSubscribe = async () => {
    if (!priceId.trim()) {
      setError('Please enter a Price ID or configure STRIPE_DEFAULT_PRICE_ID on the backend.');
      return;
    }

    setSubscribeLoading(true);
    setError(null);
    try {
      const { url } = await createCheckoutSession(priceId);
      window.location.href = url;
    } catch (err: any) {
      setError(`Subscribe failed: ${err.status || 'Unknown error'} - ${err.message}`);
    } finally {
      setSubscribeLoading(false);
    }
  };

  const handleManageBilling = async () => {
    setPortalLoading(true);
    setError(null);
    try {
      const { url } = await createPortalSession();
      window.location.href = url;
    } catch (err: any) {
      setError(`Manage billing failed: ${err.status || 'Unknown error'} - ${err.message}`);
    } finally {
      setPortalLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-md mx-auto bg-white rounded-lg shadow-md p-6">
        <h1 className="text-2xl font-bold text-gray-900 mb-6 text-center">Billing</h1>
        
        {error && (
          <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded">
            {error}
          </div>
        )}

        <div className="space-y-4">
          <div>
            <label htmlFor="priceId" className="block text-sm font-medium text-gray-700 mb-2">
              Stripe Price ID (optional if default configured)
            </label>
            <input
              id="priceId"
              type="text"
              value={priceId}
              onChange={(e) => setPriceId(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
              placeholder="price_xxx"
            />
          </div>

          <button
            onClick={handleSubscribe}
            disabled={subscribeLoading || !priceId.trim()}
            className="w-full bg-indigo-600 disabled:bg-indigo-300 text-white py-2 px-4 rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:cursor-not-allowed"
          >
            {subscribeLoading ? 'Redirecting to Checkout...' : 'Subscribe'}
          </button>

          <button
            onClick={handleManageBilling}
            disabled={portalLoading}
            className="w-full bg-green-600 disabled:bg-green-300 text-white py-2 px-4 rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 disabled:cursor-not-allowed"
          >
            {portalLoading ? 'Redirecting to Portal...' : 'Manage Billing'}
          </button>
        </div>

        <p className="mt-4 text-sm text-gray-500 text-center">
          You must be logged in to access billing features.
        </p>
      </div>
    </div>
  );
};

export default Billing;