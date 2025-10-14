import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { vi } from 'vitest';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import Account from '../pages/Account';
import { me } from '../api/auth';
import { clearToken } from '../auth/tokenStorage';
import { ClientError } from '../types/auth';

// Mock the modules
vi.mock('../api/auth', () => ({
  me: vi.fn(),
}));

vi.mock('../auth/tokenStorage', () => ({
  clearToken: vi.fn(),
}));

const mockMe = vi.mocked(me);
const mockClearToken = vi.mocked(clearToken);

// Mock window.location for hash changes
Object.defineProperty(window, 'location', {
  value: {
    hash: '',
    assign: vi.fn(),
  },
  writable: true,
});

const renderWithRouter = (ui: React.ReactElement) => render(ui, { wrapper: BrowserRouter });

describe('Account Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    window.location.hash = '#account';
  });

  it('renders loading state initially', () => {
    renderWithRouter(<Account />);
    expect(screen.getByText('Loading profile...')).toBeInTheDocument();
  });

  it('renders profile on successful me() call', async () => {
    const mockUser = {
      id: '123',
      email: 'user@example.com',
      is_active: true,
      subscription_status: 'active',
      created_at: '2023-01-01T00:00:00Z',
      updated_at: '2023-01-01T00:00:00Z',
    };
    mockMe.mockResolvedValue(mockUser);

    renderWithRouter(<Account />);

    await waitFor(() => {
      expect(screen.getByText('Account')).toBeInTheDocument();
      expect(screen.getByText('ID')).toBeInTheDocument();
      expect(screen.getByText('123')).toBeInTheDocument();
      expect(screen.getByText('Email')).toBeInTheDocument();
      expect(screen.getByText('user@example.com')).toBeInTheDocument();
      expect(screen.getByText('Active')).toBeInTheDocument();
      expect(screen.getByText('Yes')).toBeInTheDocument();
      expect(screen.getByText('Subscription Status')).toBeInTheDocument();
      expect(screen.getByText('active')).toBeInTheDocument();
      expect(screen.getByText('Created')).toBeInTheDocument();
      expect(screen.getByText('Updated')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /sign out/i })).toBeInTheDocument();
    });

    expect(mockMe).toHaveBeenCalledTimes(1);
  });

  it('redirects to login on 401 error from me()', async () => {
    const mockError = new ClientError(401, 'Not authenticated');
    mockMe.mockRejectedValue(mockError);

    renderWithRouter(<Account />);

    await waitFor(() => {
      expect(screen.getByText('Redirecting to login...')).toBeInTheDocument();
    });

    expect(window.location.hash).toBe(''); // hash cleared
    expect(mockMe).toHaveBeenCalledTimes(1);
  });

  it('shows error on non-401 error from me()', async () => {
    const mockError = new ClientError(500, 'Server error');
    mockMe.mockRejectedValue(mockError);

    renderWithRouter(<Account />);

    await waitFor(() => {
      expect(screen.getByText('Failed to load profile. Please try again.')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /sign out/i })).toBeInTheDocument();
    });

    expect(mockMe).toHaveBeenCalledTimes(1);
  });

  it('clears token and redirects on sign out click', async () => {
    const mockUser = {
      id: '123',
      email: 'user@example.com',
      is_active: true,
      subscription_status: 'active',
      created_at: '2023-01-01T00:00:00Z',
      updated_at: '2023-01-01T00:00:00Z',
    };
    mockMe.mockResolvedValue(mockUser);

    renderWithRouter(<Account />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /sign out/i })).toBeInTheDocument();
    });

    const signOutButton = screen.getByRole('button', { name: /sign out/i });
    await userEvent.click(signOutButton);

    expect(mockClearToken).toHaveBeenCalledTimes(1);
    expect(window.location.hash).toBe(''); // hash cleared
  });

  it('renders redirect note briefly on 401', async () => {
    const mockError = new ClientError(401, 'Not authenticated');
    mockMe.mockRejectedValue(mockError);

    renderWithRouter(<Account />);

    await waitFor(() => {
      expect(screen.getByText('Redirecting to login...')).toBeInTheDocument();
    });
  });
});