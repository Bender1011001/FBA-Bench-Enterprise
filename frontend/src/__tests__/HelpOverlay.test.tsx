import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { vi } from 'vitest';
import HelpOverlay from '../components/HelpOverlay';

describe('HelpOverlay Component', () => {
  const mockOnClose = vi.fn();

  afterEach(() => {
    vi.clearAllMocks();
  });

  it('does not render when open is false', () => {
    render(<HelpOverlay page="login" open={false} onClose={mockOnClose} />);

    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });

  it('renders Login help content correctly', () => {
    render(<HelpOverlay page="login" open={true} onClose={mockOnClose} />);

    expect(screen.getByText('Login Help')).toBeInTheDocument();
    expect(screen.getByText('Use your registered email and password to sign in.')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /Auth API documentation/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /Auth API documentation/i })).toHaveAttribute('href', 'https://github.com/fba-bench-enterprise/blob/main/README.md#authentication');
  });

  it('renders Register help content correctly', () => {
    render(<HelpOverlay page="register" open={true} onClose={mockOnClose} />);

    expect(screen.getByText('Register Help')).toBeInTheDocument();
    expect(screen.getByText('Create a new account with a valid email and password')).toBeInTheDocument();
    expect(screen.getByText('Password policy: At least 8 characters.')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /Auth API docs/i })).toBeInTheDocument();
  });

  it('renders Account help content correctly', () => {
    render(<HelpOverlay page="account" open={true} onClose={mockOnClose} />);

    expect(screen.getByText('Account Help')).toBeInTheDocument();
    expect(screen.getByText('View your profile details fetched via the')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /GET \/me endpoint/i })).toBeInTheDocument();
    expect(screen.getByText('JWT notes: Tokens expire after 24 hours;')).toBeInTheDocument();
  });

  it('renders Billing help content correctly', () => {
    render(<HelpOverlay page="billing" open={true} onClose={mockOnClose} />);

    expect(screen.getByText('Billing Help')).toBeInTheDocument();
    expect(screen.getByText('Manage subscriptions via Stripe integration.')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /Stripe sections/i })).toBeInTheDocument();
    expect(screen.getByText('Webhooks handle subscription events automatically.')).toBeInTheDocument();
  });

  it('calls onClose when close button is clicked', () => {
    render(<HelpOverlay page="login" open={true} onClose={mockOnClose} />);

    const closeButton = screen.getByRole('button', { name: /close/i });
    fireEvent.click(closeButton);

    expect(mockOnClose).toHaveBeenCalledTimes(1);
  });

  it('has proper accessibility attributes', () => {
    render(<HelpOverlay page="login" open={true} onClose={mockOnClose} />);

    const dialog = screen.getByRole('dialog');
    expect(dialog).toBeInTheDocument();
    expect(dialog).toHaveClass('bg-white', 'rounded-lg');

    const closeButton = screen.getByRole('button', { name: /close/i });
    expect(closeButton).toBeInTheDocument();
  });
});