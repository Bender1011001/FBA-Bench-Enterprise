import { request } from './http';

export interface CheckoutSessionRequest {
  price_id?: string;
}

export interface CheckoutSessionResponse {
  url: string;
}

export interface PortalSessionResponse {
  url: string;
}

export async function createCheckoutSession(priceId?: string): Promise<CheckoutSessionResponse> {
  const body: CheckoutSessionRequest = {};
  if (priceId) {
    body.price_id = priceId;
  }

  return request<CheckoutSessionResponse>('/billing/checkout-session', {
    method: 'POST',
    body: JSON.stringify(body),
  });
}

export async function createPortalSession(): Promise<PortalSessionResponse> {
  return request<PortalSessionResponse>('/billing/portal-session', {
    method: 'POST',
    body: JSON.stringify({}),
  });
}