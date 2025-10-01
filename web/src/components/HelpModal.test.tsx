import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import HelpModal from './HelpModal';

describe('HelpModal', () => {
  let onClose: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    onClose = vi.fn();
    vi.clearAllMocks();
  });

  it('does not render when open is false', () => {
    render(<HelpModal open={false} onClose={onClose} context="login" />);

    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });

  it('renders "How to Get Started" section in all contexts', () => {
    render(<HelpModal open={true} onClose={onClose} context="login" />);

    expect(screen.getByText('How to Get Started')).toBeInTheDocument();
    expect(screen.getByText('Register a new account or login with existing credentials.')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'POST /auth/register' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'POST /auth/login' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'billing docs' })).toBeInTheDocument();
  });

  it('renders context-specific content for login', () => {
    render(<HelpModal open={true} onClose={onClose} context="login" />);

    expect(screen.getByText('Login Help')).toBeInTheDocument();
    expect(screen.getByText('Enter your email and password to sign in.')).toBeInTheDocument();
    expect(screen.getByText('401 Invalid credentials: Check email/password.')).toBeInTheDocument();
  });

  it('renders context-specific content for billing', () => {
    render(<HelpModal open={true} onClose={onClose} context="billing" />);

    expect(screen.getByText('Billing Help')).toBeInTheDocument();
    expect(screen.getByText('Subscribe: Initiates Stripe Checkout for basic plan.')).toBeInTheDocument();
    expect(screen.getByText('Manage Billing: Opens Stripe Customer Portal for invoices/updates.')).toBeInTheDocument();
  });

  it('has correct accessibility attributes', () => {
    render(<HelpModal open={true} onClose={onClose} context="login" />);

    const modal = screen.getByRole('dialog');
    expect(modal).toHaveAttribute('aria-modal', 'true');
    expect(modal).toHaveAttribute('aria-labelledby', 'help-heading');
    expect(screen.getByLabelText('Close help modal')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Close' })).toBeInTheDocument();
  });

  it('closes on close button click', () => {
    render(<HelpModal open={true} onClose={onClose} context="login" />);

    const closeButton = screen.getByLabelText('Close help modal');
    fireEvent.click(closeButton);

    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('closes on Close button click', () => {
    render(<HelpModal open={true} onClose={onClose} context="login" />);

    const closeButton = screen.getByRole('button', { name: 'Close' });
    fireEvent.click(closeButton);

    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('closes on ESC key press', () => {
    render(<HelpModal open={true} onClose={onClose} context="login" />);

    const escEvent = new KeyboardEvent('keydown', { key: 'Escape' });
    document.dispatchEvent(escEvent);

    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('focuses on first button initially', () => {
    render(<HelpModal open={true} onClose={onClose} context="login" />);

    const firstButton = screen.getByLabelText('Close help modal');
    expect(firstButton).toHaveFocus();
  });

  it('traps focus within modal on tab navigation', () => {
    render(<HelpModal open={true} onClose={onClose} context="login" />);

    const closeXButton = screen.getByLabelText('Close help modal');
    const closeButton = screen.getByRole('button', { name: 'Close' });

    // Focus on last button
    closeButton.focus();
    const tabEvent = new KeyboardEvent('keydown', { key: 'Tab' });
    document.dispatchEvent(tabEvent);
    expect(closeXButton).toHaveFocus();

    // Shift-tab from first button
    closeXButton.focus();
    const shiftTabEvent = new KeyboardEvent('keydown', { key: 'Tab', shiftKey: true });
    document.dispatchEvent(shiftTabEvent);
    expect(closeButton).toHaveFocus();
  });
});