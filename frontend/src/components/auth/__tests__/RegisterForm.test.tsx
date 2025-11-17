import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import { RegisterForm } from '../RegisterForm';
import { createMockUseAuth } from '@/test/helpers/mockServices';
import { mockUser } from '@/test/helpers/mockData';

// Mock the AuthContext
const mockRegister = vi.fn();
const mockLogin = vi.fn();
const mockUseAuth = createMockUseAuth({
  register: mockRegister,
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
function renderRegisterForm(props = {}) {
  return render(
    <BrowserRouter>
      <RegisterForm {...props} />
    </BrowserRouter>
  );
}

describe('RegisterForm', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Rendering', () => {
    it('renders all form fields', () => {
      renderRegisterForm();

      expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/^full name$/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/^password$/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/confirm password/i)).toBeInTheDocument();
    });

    it('renders both student and teacher radio options', () => {
      renderRegisterForm();

      expect(screen.getByRole('radio', { name: /student/i })).toBeInTheDocument();
      expect(screen.getByRole('radio', { name: /teacher/i })).toBeInTheDocument();
    });

    it('renders submit button', () => {
      renderRegisterForm();

      expect(
        screen.getByRole('button', { name: /create account/i })
      ).toBeInTheDocument();
    });

    it('has proper placeholder text', () => {
      renderRegisterForm();

      expect(screen.getByPlaceholderText(/you@example.com/i)).toBeInTheDocument();
      expect(screen.getByPlaceholderText(/john doe/i)).toBeInTheDocument();
      expect(screen.getByPlaceholderText(/at least 8 characters/i)).toBeInTheDocument();
      expect(screen.getByPlaceholderText(/re-enter your password/i)).toBeInTheDocument();
    });

    it('has proper accessibility attributes', () => {
      renderRegisterForm();

      const emailInput = screen.getByLabelText(/email/i);
      expect(emailInput).toHaveAttribute('type', 'email');
      expect(emailInput).toHaveAttribute('autocomplete', 'email');

      const passwordInput = screen.getByLabelText(/^password$/i);
      expect(passwordInput).toHaveAttribute('type', 'password');
      expect(passwordInput).toHaveAttribute('autocomplete', 'new-password');
    });
  });

  describe('Form Validation', () => {
    it('shows error for invalid email format', async () => {
      const user = userEvent.setup();
      renderRegisterForm();

      const emailInput = screen.getByLabelText(/email/i);
      await user.type(emailInput, 'invalid-email');
      await user.tab();

      await waitFor(() => {
        expect(screen.getByText(/invalid email address/i)).toBeInTheDocument();
      });
    });

    it('shows error for empty name', async () => {
      const user = userEvent.setup();
      renderRegisterForm();

      const nameInput = screen.getByLabelText(/full name/i);
      await user.click(nameInput);
      await user.tab(); // Leave empty

      await waitFor(() => {
        expect(screen.getByText(/name is required/i)).toBeInTheDocument();
      });
    });

    it('shows error for name exceeding 100 characters', async () => {
      const user = userEvent.setup();
      renderRegisterForm();

      const nameInput = screen.getByLabelText(/full name/i);
      const longName = 'a'.repeat(101);
      await user.type(nameInput, longName);
      await user.tab();

      await waitFor(() => {
        expect(
          screen.getByText(/name must not exceed 100 characters/i)
        ).toBeInTheDocument();
      });
    });

    it('shows error for password less than 8 characters', async () => {
      const user = userEvent.setup();
      renderRegisterForm();

      const passwordInput = screen.getByLabelText(/^password$/i);
      await user.type(passwordInput, 'short');
      await user.tab();

      await waitFor(() => {
        expect(
          screen.getByText(/password must be at least 8 characters/i)
        ).toBeInTheDocument();
      });
    });

    it('shows error when passwords do not match', async () => {
      const user = userEvent.setup();
      renderRegisterForm();

      // Fill all required fields
      await user.type(screen.getByLabelText(/email/i), 'test@example.com');
      await user.type(screen.getByLabelText(/full name/i), 'Test User');
      await user.type(screen.getByLabelText(/^password$/i), 'password123');
      await user.type(screen.getByLabelText(/confirm password/i), 'different456');
      await user.click(screen.getByRole('radio', { name: /student/i }));

      // Trigger form submission to show error
      await user.click(screen.getByRole('button', { name: /create account/i }));

      await waitFor(() => {
        expect(screen.getByText(/passwords don't match/i)).toBeInTheDocument();
      });
    });

    it('shows no error when passwords match', async () => {
      const user = userEvent.setup();
      renderRegisterForm();

      const passwordInput = screen.getByLabelText(/^password$/i);
      const confirmInput = screen.getByLabelText(/confirm password/i);

      await user.type(passwordInput, 'password123');
      await user.type(confirmInput, 'password123');
      await user.tab();

      await waitFor(() => {
        expect(screen.queryByText(/passwords don't match/i)).not.toBeInTheDocument();
      });
    });

    it('shows error if role is not selected', async () => {
      const user = userEvent.setup();
      renderRegisterForm();

      // Fill all fields except role
      await user.type(screen.getByLabelText(/email/i), 'test@example.com');
      await user.type(screen.getByLabelText(/full name/i), 'Test User');
      await user.type(screen.getByLabelText(/^password$/i), 'password123');
      await user.type(screen.getByLabelText(/confirm password/i), 'password123');

      // Try to submit without selecting role
      await user.click(screen.getByRole('button', { name: /create account/i }));

      await waitFor(() => {
        expect(screen.getByRole('alert')).toBeInTheDocument();
      });
    });
  });

  describe('User Interactions', () => {
    it('allows typing in all text fields', async () => {
      const user = userEvent.setup();
      renderRegisterForm();

      const emailInput = screen.getByLabelText(/email/i) as HTMLInputElement;
      const nameInput = screen.getByLabelText(/full name/i) as HTMLInputElement;
      const passwordInput = screen.getByLabelText(/^password$/i) as HTMLInputElement;
      const confirmInput = screen.getByLabelText(/confirm password/i) as HTMLInputElement;

      await user.type(emailInput, 'test@example.com');
      await user.type(nameInput, 'Test User');
      await user.type(passwordInput, 'password123');
      await user.type(confirmInput, 'password123');

      expect(emailInput.value).toBe('test@example.com');
      expect(nameInput.value).toBe('Test User');
      expect(passwordInput.value).toBe('password123');
      expect(confirmInput.value).toBe('password123');
    });

    it('allows selecting student role', async () => {
      const user = userEvent.setup();
      renderRegisterForm();

      const studentRadio = screen.getByRole('radio', { name: /student/i });
      await user.click(studentRadio);

      expect(studentRadio).toBeChecked();
    });

    it('allows selecting teacher role', async () => {
      const user = userEvent.setup();
      renderRegisterForm();

      const teacherRadio = screen.getByRole('radio', { name: /teacher/i });
      await user.click(teacherRadio);

      expect(teacherRadio).toBeChecked();
    });

    it('disables entire form during submission', async () => {
      const user = userEvent.setup();
      mockRegister.mockImplementation(
        () => new Promise((resolve) => setTimeout(() => resolve(mockUser), 100))
      );
      mockLogin.mockResolvedValue(mockUser);

      renderRegisterForm();

      // Fill form
      await user.type(screen.getByLabelText(/email/i), 'test@example.com');
      await user.type(screen.getByLabelText(/full name/i), 'Test User');
      await user.type(screen.getByLabelText(/^password$/i), 'password123');
      await user.type(screen.getByLabelText(/confirm password/i), 'password123');
      await user.click(screen.getByRole('radio', { name: /student/i }));

      // Submit
      await user.click(screen.getByRole('button', { name: /create account/i }));

      // All inputs should be disabled
      expect(screen.getByLabelText(/email/i)).toBeDisabled();
      expect(screen.getByLabelText(/full name/i)).toBeDisabled();
      expect(screen.getByLabelText(/^password$/i)).toBeDisabled();
      expect(screen.getByLabelText(/confirm password/i)).toBeDisabled();
      expect(screen.getByRole('radio', { name: /student/i })).toBeDisabled();
      expect(screen.getByRole('button', { name: /creating account/i })).toBeDisabled();
    });
  });

  describe('Success Flow', () => {
    it('calls register service with form data', async () => {
      const user = userEvent.setup();
      mockRegister.mockResolvedValue(mockUser);
      mockLogin.mockResolvedValue(mockUser);

      renderRegisterForm();

      await user.type(screen.getByLabelText(/email/i), 'test@example.com');
      await user.type(screen.getByLabelText(/full name/i), 'Test User');
      await user.type(screen.getByLabelText(/^password$/i), 'password123');
      await user.type(screen.getByLabelText(/confirm password/i), 'password123');
      await user.click(screen.getByRole('radio', { name: /student/i }));
      await user.click(screen.getByRole('button', { name: /create account/i }));

      await waitFor(() => {
        expect(mockRegister).toHaveBeenCalledWith({
          email: 'test@example.com',
          name: 'Test User',
          password: 'password123',
          role: 'student',
        });
      });
    });

    it('auto-logs in after successful registration', async () => {
      const user = userEvent.setup();
      mockRegister.mockResolvedValue(mockUser);
      mockLogin.mockResolvedValue(mockUser);

      renderRegisterForm();

      await user.type(screen.getByLabelText(/email/i), 'test@example.com');
      await user.type(screen.getByLabelText(/full name/i), 'Test User');
      await user.type(screen.getByLabelText(/^password$/i), 'password123');
      await user.type(screen.getByLabelText(/confirm password/i), 'password123');
      await user.click(screen.getByRole('radio', { name: /student/i }));
      await user.click(screen.getByRole('button', { name: /create account/i }));

      await waitFor(() => {
        expect(mockLogin).toHaveBeenCalledWith({
          email: 'test@example.com',
          password: 'password123',
        });
      });
    });

    it('navigates to /dashboard after successful login', async () => {
      const user = userEvent.setup();
      mockRegister.mockResolvedValue(mockUser);
      mockLogin.mockResolvedValue(mockUser);

      renderRegisterForm();

      await user.type(screen.getByLabelText(/email/i), 'test@example.com');
      await user.type(screen.getByLabelText(/full name/i), 'Test User');
      await user.type(screen.getByLabelText(/^password$/i), 'password123');
      await user.type(screen.getByLabelText(/confirm password/i), 'password123');
      await user.click(screen.getByRole('radio', { name: /student/i }));
      await user.click(screen.getByRole('button', { name: /create account/i }));

      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith('/dashboard');
      });
    });

    it('calls onSuccess callback if provided instead of navigating', async () => {
      const user = userEvent.setup();
      const onSuccess = vi.fn();
      mockRegister.mockResolvedValue(mockUser);
      mockLogin.mockResolvedValue(mockUser);

      renderRegisterForm({ onSuccess });

      await user.type(screen.getByLabelText(/email/i), 'test@example.com');
      await user.type(screen.getByLabelText(/full name/i), 'Test User');
      await user.type(screen.getByLabelText(/^password$/i), 'password123');
      await user.type(screen.getByLabelText(/confirm password/i), 'password123');
      await user.click(screen.getByRole('radio', { name: /student/i }));
      await user.click(screen.getByRole('button', { name: /create account/i }));

      await waitFor(() => {
        expect(onSuccess).toHaveBeenCalled();
        expect(mockNavigate).not.toHaveBeenCalled();
      });
    });

    it('shows loading state during registration', async () => {
      const user = userEvent.setup();
      mockRegister.mockImplementation(
        () => new Promise((resolve) => setTimeout(() => resolve(mockUser), 100))
      );
      mockLogin.mockResolvedValue(mockUser);

      renderRegisterForm();

      await user.type(screen.getByLabelText(/email/i), 'test@example.com');
      await user.type(screen.getByLabelText(/full name/i), 'Test User');
      await user.type(screen.getByLabelText(/^password$/i), 'password123');
      await user.type(screen.getByLabelText(/confirm password/i), 'password123');
      await user.click(screen.getByRole('radio', { name: /student/i }));
      await user.click(screen.getByRole('button', { name: /create account/i }));

      // Should show loading text
      expect(screen.getByText(/creating account\.\.\./i)).toBeInTheDocument();
    });

    it('registers teacher when teacher role selected', async () => {
      const user = userEvent.setup();
      mockRegister.mockResolvedValue({ ...mockUser, role: 'teacher' });
      mockLogin.mockResolvedValue({ ...mockUser, role: 'teacher' });

      renderRegisterForm();

      await user.type(screen.getByLabelText(/email/i), 'teacher@example.com');
      await user.type(screen.getByLabelText(/full name/i), 'Test Teacher');
      await user.type(screen.getByLabelText(/^password$/i), 'password123');
      await user.type(screen.getByLabelText(/confirm password/i), 'password123');
      await user.click(screen.getByRole('radio', { name: /teacher/i }));
      await user.click(screen.getByRole('button', { name: /create account/i }));

      await waitFor(() => {
        expect(mockRegister).toHaveBeenCalledWith(
          expect.objectContaining({ role: 'teacher' })
        );
      });
    });
  });

  describe('Error Handling', () => {
    it('displays error on registration failure', async () => {
      const user = userEvent.setup();
      mockRegister.mockRejectedValue(new Error('Email already exists'));

      renderRegisterForm();

      await user.type(screen.getByLabelText(/email/i), 'existing@example.com');
      await user.type(screen.getByLabelText(/full name/i), 'Test User');
      await user.type(screen.getByLabelText(/^password$/i), 'password123');
      await user.type(screen.getByLabelText(/confirm password/i), 'password123');
      await user.click(screen.getByRole('radio', { name: /student/i }));
      await user.click(screen.getByRole('button', { name: /create account/i }));

      await waitFor(() => {
        expect(screen.getByText(/registration failed/i)).toBeInTheDocument();
      });
    });

    it('displays error on auto-login failure', async () => {
      const user = userEvent.setup();
      mockRegister.mockResolvedValue(mockUser);
      mockLogin.mockRejectedValue(new Error('Login failed'));

      renderRegisterForm();

      await user.type(screen.getByLabelText(/email/i), 'test@example.com');
      await user.type(screen.getByLabelText(/full name/i), 'Test User');
      await user.type(screen.getByLabelText(/^password$/i), 'password123');
      await user.type(screen.getByLabelText(/confirm password/i), 'password123');
      await user.click(screen.getByRole('radio', { name: /student/i }));
      await user.click(screen.getByRole('button', { name: /create account/i }));

      await waitFor(() => {
        expect(screen.getByText(/registration failed/i)).toBeInTheDocument();
      });
    });

    it('retry button re-submits with last form data', async () => {
      const user = userEvent.setup();
      mockRegister
        .mockRejectedValueOnce(new Error('Network error'))
        .mockResolvedValueOnce(mockUser);
      mockLogin.mockResolvedValue(mockUser);

      renderRegisterForm();

      await user.type(screen.getByLabelText(/email/i), 'test@example.com');
      await user.type(screen.getByLabelText(/full name/i), 'Test User');
      await user.type(screen.getByLabelText(/^password$/i), 'password123');
      await user.type(screen.getByLabelText(/confirm password/i), 'password123');
      await user.click(screen.getByRole('radio', { name: /student/i }));
      await user.click(screen.getByRole('button', { name: /create account/i }));

      // Wait for error
      await waitFor(() => {
        expect(screen.getByText(/registration failed/i)).toBeInTheDocument();
      });

      // Click retry
      const retryButton = screen.getByRole('button', { name: /try again/i });
      await user.click(retryButton);

      // Should be called twice with same data
      await waitFor(() => {
        expect(mockRegister).toHaveBeenCalledTimes(2);
        expect(mockNavigate).toHaveBeenCalledWith('/dashboard');
      });
    });
  });
});
