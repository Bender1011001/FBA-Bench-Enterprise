import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import BillingPage from './BillingPage';

vi.mock('../auth', () => ({
  useAuth: () => ({ accessToken: 'mock-token' }),
}));

describe('BillingPage', () => {
  beforeEach(() => {
    Object.defineProperty(window, 'API_BASE_URL', { value: 'http://localhost:8000' });
    localStorage.setItem('access_token', 'mock-token');
  });

  afterEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  it('test_subscribe_button_opens_checkout_url_on_success', async () => {
    const mockFetch = vi.fn();
    global.fetch = mockFetch;
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ url: 'https://checkout.stripe.com/test' }),
    } as Response);

    render(<BillingPage />);
    const subscribeButton = screen.getByRole('button', { name: /subscribe/i });
    fireEvent.click(subscribeButton);

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/billing/checkout-session',
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            'Authorization': 'Bearer mock-token',
          }),
        })
      );
      expect(window.location.href).toBe('https://checkout.stripe.com/test');
    });
  });

  it('test_manage_billing_button_opens_portal_url_on_success', async () => {
    const mockFetch = vi.fn();
    global.fetch = mockFetch;
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ url: 'https://billing.stripe.com/portal' }),
    } as Response);

    render(<BillingPage />);
    const manageButton = screen.getByRole('button', { name: /manage billing/i });
    fireEvent.click(manageButton);

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/billing/portal-session',
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            'Authorization': 'Bearer mock-token',
          }),
        })
      );
      expect(window.location.href).toBe('https://billing.stripe.com/portal');
    });
  });

  it('test_manage_billing_404_shows_guidance_message', async () => {
    const mockFetch = vi.fn();
    global.fetch = mockFetch;
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 404,
      json: async () => ({ detail: 'No Stripe customer found' }),
    } as Response);

    render(<BillingPage />);
    const manageButton = screen.getByRole('button', { name: /manage billing/i });
    fireEvent.click(manageButton);

    await waitFor(() => {
      expect(screen.getByText('No billing account found. Please subscribe first.')).toBeInTheDocument();
    });
  });

  it('test_buttons_disable_during_loading_and_restore_after', async () => {
    const mockFetch = vi.fn();
    global.fetch = mockFetch;
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({}),
    } as Response);

    render(<BillingPage />);
    const subscribeButton = screen.getByRole('button', { name: /subscribe/i });

    fireEvent.click(subscribeButton);
    expect(subscribeButton).toBeDisabled();
    expect(subscribeButton).toHaveTextContent('Loading...');

    await waitFor(() => {
      expect(subscribeButton).not.toBeDisabled();
      expect(subscribeButton).toHaveTextContent('Subscribe');
    });
  });
});