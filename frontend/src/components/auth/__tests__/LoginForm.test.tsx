import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import { LoginForm } from '../LoginForm';
import { createMockUseAuth } from '@/test/helpers/mockServices';
import { mockUser } from '@/test/helpers/mockData';

// Mock the AuthContext
const mockLogin = vi.fn();
const mockUseAuth = createMockUseAuth({
  login: mockLogin,
});

vi.mock('@/contexts/AuthContext', () => ({
  useAuth: () => mockUseAuth,
}));

// Mock useNavigate
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

// Helper to render with Router
function renderLoginForm(props = {}) {
  return render(
    <BrowserRouter>
      <LoginForm {...props} />
    </BrowserRouter>
  );
}

describe('LoginForm', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Rendering', () => {
    it('renders email and password inputs', () => {
      renderLoginForm();

      expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
    });

    it('renders submit button', () => {
      renderLoginForm();

      expect(screen.getByRole('button', { name: /log in/i })).toBeInTheDocument();
    });

    it('renders with proper accessibility attributes', () => {
      renderLoginForm();

      const emailInput = screen.getByLabelText(/email/i);
      expect(emailInput).toHaveAttribute('type', 'email');
      expect(emailInput).toHaveAttribute('autocomplete', 'email');

      const passwordInput = screen.getByLabelText(/password/i);
      expect(passwordInput).toHaveAttribute('type', 'password');
      expect(passwordInput).toHaveAttribute('autocomplete', 'current-password');
    });

    it('has placeholder text for inputs', () => {
      renderLoginForm();

      expect(screen.getByPlaceholderText(/you@example.com/i)).toBeInTheDocument();
      expect(screen.getByPlaceholderText(/enter your password/i)).toBeInTheDocument();
    });
  });

  describe('Form Validation', () => {
    it('shows error for invalid email format', async () => {
      const user = userEvent.setup();
      renderLoginForm();

      const emailInput = screen.getByLabelText(/email/i);
      await user.type(emailInput, 'invalid-email');
      await user.tab(); // Trigger blur event

      await waitFor(() => {
        expect(screen.getByText(/invalid email address/i)).toBeInTheDocument();
      });
    });

    it('shows error for password less than 8 characters', async () => {
      const user = userEvent.setup();
      renderLoginForm();

      const passwordInput = screen.getByLabelText(/password/i);
      await user.type(passwordInput, 'short');
      await user.tab(); // Trigger blur event

      await waitFor(() => {
        expect(
          screen.getByText(/password must be at least 8 characters/i)
        ).toBeInTheDocument();
      });
    });

    it('shows error for password exceeding 100 characters', async () => {
      const user = userEvent.setup();
      renderLoginForm();

      const passwordInput = screen.getByLabelText(/password/i);
      const longPassword = 'a'.repeat(101);
      await user.type(passwordInput, longPassword);
      await user.tab();

      await waitFor(() => {
        expect(
          screen.getByText(/password must not exceed 100 characters/i)
        ).toBeInTheDocument();
      });
    });

    it('clears validation errors when corrected', async () => {
      const user = userEvent.setup();
      renderLoginForm();

      const emailInput = screen.getByLabelText(/email/i);

      // Enter invalid email
      await user.type(emailInput, 'invalid');
      await user.tab();

      await waitFor(() => {
        expect(screen.getByText(/invalid email address/i)).toBeInTheDocument();
      });

      // Clear and enter valid email
      await user.clear(emailInput);
      await user.type(emailInput, 'valid@example.com');
      await user.tab();

      await waitFor(() => {
        expect(screen.queryByText(/invalid email address/i)).not.toBeInTheDocument();
      });
    });
  });

  describe('User Interactions', () => {
    it('allows typing in email and password fields', async () => {
      const user = userEvent.setup();
      renderLoginForm();

      const emailInput = screen.getByLabelText(/email/i) as HTMLInputElement;
      const passwordInput = screen.getByLabelText(/password/i) as HTMLInputElement;

      await user.type(emailInput, 'test@example.com');
      await user.type(passwordInput, 'password123');

      expect(emailInput.value).toBe('test@example.com');
      expect(passwordInput.value).toBe('password123');
    });

    it('disables form inputs during submission', async () => {
      const user = userEvent.setup();
      mockLogin.mockImplementation(
        () => new Promise((resolve) => setTimeout(() => resolve(mockUser), 100))
      );

      renderLoginForm();

      const emailInput = screen.getByLabelText(/email/i);
      const passwordInput = screen.getByLabelText(/password/i);
      const submitButton = screen.getByRole('button', { name: /log in/i });

      await user.type(emailInput, 'test@example.com');
      await user.type(passwordInput, 'password123');
      await user.click(submitButton);

      // Check inputs are disabled during submission
      expect(emailInput).toBeDisabled();
      expect(passwordInput).toBeDisabled();
      expect(submitButton).toBeDisabled();
    });
  });

  describe('Success Flow', () => {
    it('calls login service with correct credentials on submit', async () => {
      const user = userEvent.setup();
      mockLogin.mockResolvedValue(mockUser);

      renderLoginForm();

      await user.type(screen.getByLabelText(/email/i), 'test@example.com');
      await user.type(screen.getByLabelText(/password/i), 'password123');
      await user.click(screen.getByRole('button', { name: /log in/i }));

      await waitFor(() => {
        expect(mockLogin).toHaveBeenCalledWith({
          email: 'test@example.com',
          password: 'password123',
        });
      });
    });

    it('navigates to /dashboard on successful login', async () => {
      const user = userEvent.setup();
      mockLogin.mockResolvedValue(mockUser);

      renderLoginForm();

      await user.type(screen.getByLabelText(/email/i), 'test@example.com');
      await user.type(screen.getByLabelText(/password/i), 'password123');
      await user.click(screen.getByRole('button', { name: /log in/i }));

      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith('/dashboard');
      });
    });

    it('calls onSuccess callback if provided instead of navigating', async () => {
      const user = userEvent.setup();
      const onSuccess = vi.fn();
      mockLogin.mockResolvedValue(mockUser);

      renderLoginForm({ onSuccess });

      await user.type(screen.getByLabelText(/email/i), 'test@example.com');
      await user.type(screen.getByLabelText(/password/i), 'password123');
      await user.click(screen.getByRole('button', { name: /log in/i }));

      await waitFor(() => {
        expect(onSuccess).toHaveBeenCalled();
        expect(mockNavigate).not.toHaveBeenCalled();
      });
    });

    it('shows loading state during login', async () => {
      const user = userEvent.setup();
      mockLogin.mockImplementation(
        () => new Promise((resolve) => setTimeout(() => resolve(mockUser), 100))
      );

      renderLoginForm();

      await user.type(screen.getByLabelText(/email/i), 'test@example.com');
      await user.type(screen.getByLabelText(/password/i), 'password123');
      await user.click(screen.getByRole('button', { name: /log in/i }));

      // Should show loading text
      expect(screen.getByText(/logging in\.\.\./i)).toBeInTheDocument();
    });
  });

  describe('Error Handling', () => {
    it('displays error message on login failure', async () => {
      const user = userEvent.setup();
      mockLogin.mockRejectedValue(new Error('Invalid credentials'));

      renderLoginForm();

      await user.type(screen.getByLabelText(/email/i), 'test@example.com');
      await user.type(screen.getByLabelText(/password/i), 'wrongpassword');
      await user.click(screen.getByRole('button', { name: /log in/i }));

      await waitFor(() => {
        expect(screen.getByText(/login failed/i)).toBeInTheDocument();
      });
    });

    it('shows retry button on error', async () => {
      const user = userEvent.setup();
      mockLogin.mockRejectedValue(new Error('Network error'));

      renderLoginForm();

      await user.type(screen.getByLabelText(/email/i), 'test@example.com');
      await user.type(screen.getByLabelText(/password/i), 'password123');
      await user.click(screen.getByRole('button', { name: /log in/i }));

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /try again/i })).toBeInTheDocument();
      });
    });

    it('retry button calls login again with same credentials', async () => {
      const user = userEvent.setup();
      mockLogin
        .mockRejectedValueOnce(new Error('Network error'))
        .mockResolvedValueOnce(mockUser);

      renderLoginForm();

      await user.type(screen.getByLabelText(/email/i), 'test@example.com');
      await user.type(screen.getByLabelText(/password/i), 'password123');
      await user.click(screen.getByRole('button', { name: /log in/i }));

      // Wait for error to appear
      await waitFor(() => {
        expect(screen.getByText(/login failed/i)).toBeInTheDocument();
      });

      // Click retry
      const retryButton = screen.getByRole('button', { name: /try again/i });
      await user.click(retryButton);

      // Login should be called again
      await waitFor(() => {
        expect(mockLogin).toHaveBeenCalledTimes(2);
        expect(mockNavigate).toHaveBeenCalledWith('/dashboard');
      });
    });

    it('does not submit form with validation errors', async () => {
      const user = userEvent.setup();
      renderLoginForm();

      // Only fill email, leave password empty
      await user.type(screen.getByLabelText(/email/i), 'test@example.com');
      await user.click(screen.getByRole('button', { name: /log in/i }));

      // Login should not be called
      expect(mockLogin).not.toHaveBeenCalled();
    });
  });
});
