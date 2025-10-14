import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi } from 'vitest';
import Login from '../pages/Login';
import { login } from '../api/auth';
import { ClientError } from '../types/auth';

// Mock the login function
vi.mock('../pages/../api/auth', () => ({
  login: vi.fn(),
}));

const mockLogin = vi.mocked(login);

describe('Login Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders login form with email and password fields', () => {
    render(<Login />);
    expect(screen.getByPlaceholderText('Email address')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Password')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument();
  });

  it('disables submit button when email is invalid', async () => {
    const user = userEvent.setup();
    render(<Login />);

    const emailInput = screen.getByPlaceholderText('Email address');
    const passwordInput = screen.getByPlaceholderText('Password');
    const submitButton = screen.getByRole('button', { name: /sign in/i });

    // Invalid email, valid password
    await user.type(emailInput, 'invalid-email');
    await user.type(passwordInput, 'password12345678'); // 16 chars > 8

    expect(submitButton).toBeDisabled();
    expect(screen.getByText('Email must be a valid format.')).toBeInTheDocument();
  });

  it('disables submit button when password is too short', async () => {
    const user = userEvent.setup();
    render(<Login />);

    const emailInput = screen.getByPlaceholderText('Email address');
    const passwordInput = screen.getByPlaceholderText('Password');
    const submitButton = screen.getByRole('button', { name: /sign in/i });

    // Valid email, short password
    await user.type(emailInput, 'user@example.com');
    await user.type(passwordInput, 'short'); // 5 chars < 8

    expect(submitButton).toBeDisabled();
    expect(screen.getByText('Password must be at least 8 characters.')).toBeInTheDocument();
  });

  it('enables submit button when form is valid', async () => {
    const user = userEvent.setup();
    render(<Login />);

    const emailInput = screen.getByPlaceholderText('Email address');
    const passwordInput = screen.getByPlaceholderText('Password');
    const submitButton = screen.getByRole('button', { name: /sign in/i });

    await user.type(emailInput, 'user@example.com');
    await user.type(passwordInput, 'password12345678'); // 16 chars

    expect(submitButton).not.toBeDisabled();
    expect(screen.queryByText('Email must be a valid format.')).not.toBeInTheDocument();
    expect(screen.queryByText('Password must be at least 8 characters.')).not.toBeInTheDocument();
  });

  it('shows loading state during submission', async () => {
    const user = userEvent.setup();
    mockLogin.mockImplementation(() => new Promise(resolve => setTimeout(resolve, 100)));

    render(<Login />);

    const emailInput = screen.getByPlaceholderText('Email address');
    const passwordInput = screen.getByPlaceholderText('Password');
    const submitButton = screen.getByRole('button', { name: /sign in/i });

    await user.type(emailInput, 'user@example.com');
    await user.type(passwordInput, 'password12345678');

    await user.click(submitButton);

    expect(submitButton).toBeDisabled();
    expect(screen.getByText('Signing in...')).toBeInTheDocument();
  });

  it('calls login on valid form submission and shows success state', async () => {
    const user = userEvent.setup();
    mockLogin.mockResolvedValue({ access_token: 'mock-token', token_type: 'bearer' });

    render(<Login />);

    const emailInput = screen.getByPlaceholderText('Email address');
    const passwordInput = screen.getByPlaceholderText('Password');
    const submitButton = screen.getByRole('button', { name: /sign in/i });

    await user.type(emailInput, 'user@example.com');
    await user.type(passwordInput, 'password12345678');

    await user.click(submitButton);

    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith({ email: 'user@example.com', password: 'password12345678' });
    });

    expect(screen.getByText('Logged in')).toBeInTheDocument();
    expect(screen.getByText('Access token has been stored successfully.')).toBeInTheDocument();
  });

  it('shows error message on login failure with 401', async () => {
    const user = userEvent.setup();
    const mockError = new ClientError(401, 'Invalid credentials');
    mockLogin.mockRejectedValue(mockError);

    render(<Login />);

    const emailInput = screen.getByPlaceholderText('Email address');
    const passwordInput = screen.getByPlaceholderText('Password');
    const submitButton = screen.getByRole('button', { name: /sign in/i });

    await user.type(emailInput, 'user@example.com');
    await user.type(passwordInput, 'password12345678');

    await user.click(submitButton);

    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith({ email: 'user@example.com', password: 'password12345678' });
    });

    expect(screen.getByText('401: Invalid credentials')).toBeInTheDocument();
    expect(submitButton).not.toBeDisabled(); // Button should be enabled after error
  });

  it('shows generic error on unexpected error', async () => {
    const user = userEvent.setup();
    mockLogin.mockRejectedValue(new Error('Network error'));

    render(<Login />);

    const emailInput = screen.getByPlaceholderText('Email address');
    const passwordInput = screen.getByPlaceholderText('Password');
    const submitButton = screen.getByRole('button', { name: /sign in/i });

    await user.type(emailInput, 'user@example.com');
    await user.type(passwordInput, 'password12345678');

    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText('An unexpected error occurred. Please try again.')).toBeInTheDocument();
    });
  });

  it('clears error message when user starts typing', async () => {
    const user = userEvent.setup();
    const mockError = new ClientError(401, 'Invalid credentials');
    mockLogin.mockRejectedValue(mockError);

    render(<Login />);

    const emailInput = screen.getByPlaceholderText('Email address');
    const passwordInput = screen.getByPlaceholderText('Password');
    const submitButton = screen.getByRole('button', { name: /sign in/i });

    await user.type(emailInput, 'user@example.com');
    await user.type(passwordInput, 'password12345678');

    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText('401: Invalid credentials')).toBeInTheDocument();
    });

    // Type in email to clear error
    await user.type(emailInput, 'a');
    expect(screen.queryByText('401: Invalid credentials')).not.toBeInTheDocument();
  });
});