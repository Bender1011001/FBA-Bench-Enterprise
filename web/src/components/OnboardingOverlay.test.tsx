import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import OnboardingOverlay from './OnboardingOverlay';

describe('OnboardingOverlay', () => {
  let onClose: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    onClose = vi.fn();
    localStorage.clear();
    vi.clearAllMocks();
  });

  it('renders welcome message and quick steps', () => {
    render(<OnboardingOverlay onClose={onClose} />);

    expect(screen.getByText('Welcome to FBA Enterprise Sandbox')).toBeInTheDocument();
    expect(screen.getByText('Configure window.API_BASE_URL in index.html')).toBeInTheDocument();
    expect(screen.getByText('Register or login')).toBeInTheDocument();
    expect(screen.getByText('Use Billing to subscribe/manage if desired')).toBeInTheDocument();
  });

  it('has correct accessibility attributes', () => {
    render(<OnboardingOverlay onClose={onClose} />);

    const overlay = screen.getByRole('dialog');
    expect(overlay).toHaveAttribute('aria-modal', 'true');
    expect(overlay).toHaveAttribute('aria-labelledby', 'onboarding-heading');
    expect(screen.getByRole('button', { name: 'Dismiss' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Get started' })).toBeInTheDocument();
    expect(screen.getByLabelText('Close onboarding')).toBeInTheDocument();
  });

  it('calls onClose and sets localStorage on "Dismiss" click', () => {
    render(<OnboardingOverlay onClose={onClose} />);

    const dismissButton = screen.getByRole('button', { name: 'Dismiss' });
    fireEvent.click(dismissButton);

    expect(onClose).toHaveBeenCalledTimes(1);
    expect(localStorage.getItem('fbaee_onboarding_dismissed')).toBe('true');
  });

  it('calls onClose and sets localStorage on "Get started" click', () => {
    render(<OnboardingOverlay onClose={onClose} />);

    const getStartedButton = screen.getByRole('button', { name: 'Get started' });
    fireEvent.click(getStartedButton);

    expect(onClose).toHaveBeenCalledTimes(1);
    expect(localStorage.getItem('fbaee_onboarding_dismissed')).toBe('true');
  });

  it('calls onClose and sets localStorage on close button click', () => {
    render(<OnboardingOverlay onClose={onClose} />);

    const closeButton = screen.getByLabelText('Close onboarding');
    fireEvent.click(closeButton);

    expect(onClose).toHaveBeenCalledTimes(1);
    expect(localStorage.getItem('fbaee_onboarding_dismissed')).toBe('true');
  });

  it('closes on ESC key press', () => {
    render(<OnboardingOverlay onClose={onClose} />);

    const escEvent = new KeyboardEvent('keydown', { key: 'Escape' });
    document.dispatchEvent(escEvent);

    expect(onClose).toHaveBeenCalledTimes(1);
    expect(localStorage.getItem('fbaee_onboarding_dismissed')).toBe('true');
  });

  it('focuses on first button initially', () => {
    const { container } = render(<OnboardingOverlay onClose={onClose} />);

    const firstButton = screen.getByRole('button', { name: 'Dismiss' });
    expect(firstButton).toHaveFocus();
  });

  it('traps focus within modal on tab navigation', () => {
    render(<OnboardingOverlay onClose={onClose} />);

    const dismissButton = screen.getByRole('button', { name: 'Dismiss' });
    const getStartedButton = screen.getByRole('button', { name: 'Get started' });
    const closeButton = screen.getByLabelText('Close onboarding');

    // Focus on last button
    getStartedButton.focus();
    const tabEvent = new KeyboardEvent('keydown', { key: 'Tab' });
    document.dispatchEvent(tabEvent);
    expect(dismissButton).toHaveFocus();

    // Shift-tab from first button
    dismissButton.focus();
    const shiftTabEvent = new KeyboardEvent('keydown', { key: 'Tab', shiftKey: true });
    document.dispatchEvent(shiftTabEvent);
    expect(getStartedButton).toHaveFocus();
  });
});