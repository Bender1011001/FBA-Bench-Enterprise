import { useState } from 'react'

interface ApiError {
  detail: string
}

const BillingPage: React.FC = () => {
  const [subscribeLoading, setSubscribeLoading] = useState<boolean>(false)
  const [manageLoading, setManageLoading] = useState<boolean>(false)
  const [error, setError] = useState<string | null>(null)

  const apiBaseUrl = (window as any).API_BASE_URL || 'http://127.0.0.1:8000'
  const accessToken = localStorage.getItem('access_token')

  const handleSubscribe = async () => {
    if (!accessToken) {
      setError('Authentication required. Please log in.')
      return
    }

    setSubscribeLoading(true)
    setError(null)

    try {
      const response = await fetch(`${apiBaseUrl}/billing/checkout-session`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${accessToken}`
        },
        body: JSON.stringify({})
      })

      if (!response.ok) {
        const errorData: ApiError = await response.json()
        throw new Error(errorData.detail || `HTTP ${response.status}`)
      }

      const data = await response.json()
      if (data.url) {
        window.location.href = data.url
      } else {
        setError('Unexpected response from server.')
      }
    } catch (err: any) {
      setError(err.message || 'An error occurred. Please try again.')
    } finally {
      setSubscribeLoading(false)
    }
  }

  const handleManageBilling = async () => {
    if (!accessToken) {
      setError('Authentication required. Please log in.')
      return
    }

    setManageLoading(true)
    setError(null)

    try {
      const response = await fetch(`${apiBaseUrl}/billing/portal-session`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${accessToken}`
        },
        body: JSON.stringify({})
      })

      if (!response.ok) {
        const errorData: ApiError = await response.json()
        if (response.status === 404) {
          setError('No billing account found. Please subscribe first.')
        } else if (response.status === 503) {
          setError('Billing is currently unavailable.')
        } else {
          throw new Error(errorData.detail || `HTTP ${response.status}`)
        }
        return
      }

      const data = await response.json()
      if (data.url) {
        window.location.href = data.url
      } else {
        setError('Unexpected response from server.')
      }
    } catch (err: any) {
      setError(err.message || 'Billing is currently unavailable.')
    } finally {
      setManageLoading(false)
    }
  }

  return (
    <div className="card">
      <h2>Billing Management</h2>
      {error && (
        <div className="error" style={{ marginBottom: '1rem', padding: '1rem', backgroundColor: '#ffe6e6', borderRadius: '6px' }}>
          {error}
        </div>
      )}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        <button
          onClick={handleSubscribe}
          disabled={subscribeLoading}
          className="btn btn-primary"
          aria-busy={subscribeLoading}
        >
          {subscribeLoading ? 'Loading...' : 'Subscribe'}
        </button>
        <button
          onClick={handleManageBilling}
          disabled={manageLoading}
          className="btn btn-secondary"
          aria-busy={manageLoading}
        >
          {manageLoading ? 'Loading...' : 'Manage Billing'}
        </button>
      </div>
      <p style={{ marginTop: '1rem', fontSize: '0.875rem', color: '#6c757d' }}>
        Click "Subscribe" to start a new subscription via Stripe Checkout.
        Click "Manage Billing" to access your customer portal for invoices and payment updates.
      </p>
    </div>
  )
}

export default BillingPage