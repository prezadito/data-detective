import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { useApi } from '@/hooks/useApi';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import { ErrorMessage } from '@/components/ui/ErrorMessage';
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

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
    mode: 'onBlur',
  });

  const { isLoading, error, retry, execute: performLogin } = useApi(login, {
    successMessage: 'Welcome back!',
    showErrorToast: false, // We'll show errors inline instead
    onSuccess: () => {
      if (onSuccess) {
        onSuccess();
      } else {
        navigate('/dashboard');
      }
    },
  });

  const onSubmit = async (data: LoginFormData) => {
    const credentials: LoginCredentials = {
      email: data.email,
      password: data.password,
    };

    await performLogin(credentials);
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      {error ? (
        <ErrorMessage
          error={error}
          title="Login failed"
          onRetry={retry}
        />
      ) : null}
      <Input
        {...register('email')}
        type="email"
        label="Email"
        placeholder="you@example.com"
        error={errors.email?.message}
        autoComplete="email"
        disabled={isLoading}
      />

      <Input
        {...register('password')}
        type="password"
        label="Password"
        placeholder="Enter your password"
        error={errors.password?.message}
        autoComplete="current-password"
        disabled={isLoading}
      />

      <Button
        type="submit"
        variant="primary"
        size="lg"
        className="w-full"
        isLoading={isLoading}
        disabled={isLoading}
      >
        {isLoading ? 'Logging in...' : 'Log In'}
      </Button>
    </form>
  );
}
