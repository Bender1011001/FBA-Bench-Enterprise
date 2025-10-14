import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi } from 'vitest';
import Register from '../pages/Register';
import { register } from '../api/auth';
import { ClientError } from '../types/auth';

// Mock the register function
vi.mock('../api/auth', () => ({
  register: vi.fn(),
}));

const mockRegister = vi.mocked(register);

describe('Register Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders register form with email and password fields', () => {
    render(<Register />);
    expect(screen.getByPlaceholderText('Email address')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Password')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /register/i })).toBeInTheDocument();
  });

  it('disables submit button when email is invalid', async () => {
    const user = userEvent.setup();
    render(<Register />);

    const emailInput = screen.getByPlaceholderText('Email address');
    const passwordInput = screen.getByPlaceholderText('Password');
    const submitButton = screen.getByRole('button', { name: /register/i });

    // Invalid email, valid password
    await user.type(emailInput, 'invalid-email');
    await user.type(passwordInput, 'password12345678'); // 16 chars > 8

    expect(submitButton).toBeDisabled();
    expect(screen.getByText('Email must be a valid format.')).toBeInTheDocument();
  });

  it('disables submit button when password is too short', async () => {
    const user = userEvent.setup();
    render(<Register />);

    const emailInput = screen.getByPlaceholderText('Email address');
    const passwordInput = screen.getByPlaceholderText('Password');
    const submitButton = screen.getByRole('button', { name: /register/i });

    // Valid email, short password
    await user.type(emailInput, 'user@example.com');
    await user.type(passwordInput, 'short'); // 5 chars < 8

    expect(submitButton).toBeDisabled();
    expect(screen.getByText('Password must be at least 8 characters.')).toBeInTheDocument();
  });

  it('enables submit button when form is valid', async () => {
    const user = userEvent.setup();
    render(<Register />);

    const emailInput = screen.getByPlaceholderText('Email address');
    const passwordInput = screen.getByPlaceholderText('Password');
    const submitButton = screen.getByRole('button', { name: /register/i });

    await user.type(emailInput, 'user@example.com');
    await user.type(passwordInput, 'password12345678'); // 16 chars

    expect(submitButton).not.toBeDisabled();
    expect(screen.queryByText('Email must be a valid format.')).not.toBeInTheDocument();
    expect(screen.queryByText('Password must be at least 8 characters.')).not.toBeInTheDocument();
  });

  it('shows loading state during submission', async () => {
    const user = userEvent.setup();
    mockRegister.mockImplementation(() => new Promise(resolve => setTimeout(resolve, 100)));

    render(<Register />);

    const emailInput = screen.getByPlaceholderText('Email address');
    const passwordInput = screen.getByPlaceholderText('Password');
    const submitButton = screen.getByRole('button', { name: /register/i });

    await user.type(emailInput, 'user@example.com');
    await user.type(passwordInput, 'password12345678');

    await user.click(submitButton);

    expect(submitButton).toBeDisabled();
    expect(screen.getByText('Registering...')).toBeInTheDocument();
  });

  it('calls register on valid form submission and shows success state', async () => {
    const user = userEvent.setup();
    mockRegister.mockResolvedValue({
      id: 'd9c44e0a-1a5b-4b46-a8b1-6c6d6e5e9b1a',
      email: 'user@example.com',
      is_active: true,
      subscription_status: '',
      created_at: '2025-09-29T08:00:00Z',
      updated_at: '2025-09-29T08:00:00Z'
    });

    render(<Register />);

    const emailInput = screen.getByPlaceholderText('Email address');
    const passwordInput = screen.getByPlaceholderText('Password');
    const submitButton = screen.getByRole('button', { name: /register/i });

    await user.type(emailInput, 'user@example.com');
    await user.type(passwordInput, 'password12345678');

    await user.click(submitButton);

    await waitFor(() => {
      expect(mockRegister).toHaveBeenCalledWith({ email: 'user@example.com', password: 'password12345678' });
    });

    expect(screen.getByText('Registered')).toBeInTheDocument();
    expect(screen.getByText('Registration completed successfully.')).toBeInTheDocument();
  });

  it('shows error message on duplicate email with 409', async () => {
    const user = userEvent.setup();
    const mockError = new ClientError(409, 'Email already registered');
    mockRegister.mockRejectedValue(mockError);

    render(<Register />);

    const emailInput = screen.getByPlaceholderText('Email address');
    const passwordInput = screen.getByPlaceholderText('Password');
    const submitButton = screen.getByRole('button', { name: /register/i });

    await user.type(emailInput, 'user@example.com');
    await user.type(passwordInput, 'password12345678');

    await user.click(submitButton);

    await waitFor(() => {
      expect(mockRegister).toHaveBeenCalledWith({ email: 'user@example.com', password: 'password12345678' });
    });

    expect(screen.getByText('409: Email already registered')).toBeInTheDocument();
    expect(submitButton).not.toBeDisabled(); // Button should be enabled after error
  });

  it('shows generic error on unexpected error', async () => {
    const user = userEvent.setup();
    mockRegister.mockRejectedValue(new Error('Network error'));

    render(<Register />);

    const emailInput = screen.getByPlaceholderText('Email address');
    const passwordInput = screen.getByPlaceholderText('Password');
    const submitButton = screen.getByRole('button', { name: /register/i });

    await user.type(emailInput, 'user@example.com');
    await user.type(passwordInput, 'password12345678');

    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText('An unexpected error occurred. Please try again.')).toBeInTheDocument();
    });
  });

  it('clears error message when user starts typing', async () => {
    const user = userEvent.setup();
    const mockError = new ClientError(409, 'Email already registered');
    mockRegister.mockRejectedValue(mockError);

    render(<Register />);

    const emailInput = screen.getByPlaceholderText('Email address');
    const passwordInput = screen.getByPlaceholderText('Password');
    const submitButton = screen.getByRole('button', { name: /register/i });

    await user.type(emailInput, 'user@example.com');
    await user.type(passwordInput, 'password12345678');

    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText('409: Email already registered')).toBeInTheDocument();
    });

    // Type in email to clear error
    await user.type(emailInput, 'a');
    expect(screen.queryByText('409: Email already registered')).not.toBeInTheDocument();
  });
});