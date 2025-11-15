import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import type { LoginCredentials } from '@/types';

// Validation schema matching backend requirements
const loginSchema = z.object({
  email: z.string().email('Invalid email address'),
  password: z
    .string()
    .min(8, 'Password must be at least 8 characters')
    .max(100, 'Password must not exceed 100 characters'),
});

type LoginFormData = z.infer<typeof loginSchema>;

interface LoginFormProps {
  onSuccess?: () => void;
}

export function LoginForm({ onSuccess }: LoginFormProps) {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [apiError, setApiError] = useState<string>('');

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
    mode: 'onBlur',
  });

  const onSubmit = async (data: LoginFormData) => {
    try {
      setApiError('');
      const credentials: LoginCredentials = {
        email: data.email,
        password: data.password,
      };

      await login(credentials);

      // Call success callback or navigate to dashboard
      if (onSuccess) {
        onSuccess();
      } else {
        navigate('/dashboard');
      }
    } catch (error) {
      // Handle ky HTTPError
      if (error && typeof error === 'object' && 'response' in error) {
        try {
          const kyError = error as { response: Response };
          const errorData = await kyError.response.json() as { detail?: string };
          setApiError(errorData.detail || 'Login failed. Please try again.');
        } catch {
          setApiError('Login failed. Please try again.');
        }
      } else if (error instanceof Error) {
        // Network errors (connection refused, timeout, etc.)
        if (error.name === 'TypeError' || error.message.includes('fetch') || error.message.includes('network')) {
          setApiError('Cannot connect to server. Make sure the backend is running at http://localhost:8000');
        } else {
          setApiError(error.message);
        }
      } else {
        setApiError('An unexpected error occurred. Please try again.');
      }
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      {apiError && (
        <div
          className="p-4 bg-red-50 border border-red-200 rounded-md"
          role="alert"
          aria-live="assertive"
        >
          <p className="text-sm text-red-800">{apiError}</p>
        </div>
      )}

      <Input
        {...register('email')}
        type="email"
        label="Email"
        placeholder="you@example.com"
        error={errors.email?.message}
        autoComplete="email"
        disabled={isSubmitting}
      />

      <Input
        {...register('password')}
        type="password"
        label="Password"
        placeholder="Enter your password"
        error={errors.password?.message}
        autoComplete="current-password"
        disabled={isSubmitting}
      />

      <Button
        type="submit"
        variant="primary"
        size="lg"
        className="w-full"
        isLoading={isSubmitting}
        disabled={isSubmitting}
      >
        {isSubmitting ? 'Logging in...' : 'Log In'}
      </Button>
    </form>
  );
}
