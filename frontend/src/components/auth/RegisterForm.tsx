import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import { ErrorMessage } from '@/components/ui/ErrorMessage';
import { parseApiError } from '@/utils/errors';
import type { RegisterData, LoginCredentials, UserRole } from '@/types';

// Validation schema matching backend requirements
const registerSchema = z.object({
  email: z.string().email('Invalid email address'),
  name: z.string()
    .min(1, 'Name is required')
    .max(100, 'Name must not exceed 100 characters'),
  password: z.string()
    .min(8, 'Password must be at least 8 characters')
    .max(100, 'Password must not exceed 100 characters'),
  confirmPassword: z.string(),
  role: z.enum(['student', 'teacher']),
}).refine((data) => data.password === data.confirmPassword, {
  message: "Passwords don't match",
  path: ['confirmPassword'],
});

type RegisterFormData = z.infer<typeof registerSchema>;

interface RegisterFormProps {
  onSuccess?: () => void;
}

export function RegisterForm({ onSuccess }: RegisterFormProps) {
  const navigate = useNavigate();
  const { register: registerUser, login } = useAuth();
  const [apiError, setApiError] = useState<unknown | null>(null);
  const [lastFormData, setLastFormData] = useState<RegisterFormData | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<RegisterFormData>({
    resolver: zodResolver(registerSchema),
    mode: 'onBlur',
  });

  const onSubmit = async (data: RegisterFormData) => {
    try {
      setApiError(null);
      setLastFormData(data);

      // Step 1: Register user
      const registerData: RegisterData = {
        email: data.email,
        name: data.name,
        password: data.password,
        role: data.role as UserRole,
      };

      await registerUser(registerData);

      // Step 2: Auto-login with same credentials
      const loginCredentials: LoginCredentials = {
        email: data.email,
        password: data.password,
      };

      await login(loginCredentials);

      // Step 3: Navigate to dashboard or call success callback
      if (onSuccess) {
        onSuccess();
      } else {
        navigate('/dashboard');
      }
    } catch (error) {
      setApiError(error);
    }
  };

  const handleRetry = () => {
    if (lastFormData) {
      onSubmit(lastFormData);
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      {apiError && (
        <ErrorMessage
          error={apiError}
          title="Registration failed"
          onRetry={handleRetry}
        />
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
        {...register('name')}
        type="text"
        label="Full Name"
        placeholder="John Doe"
        error={errors.name?.message}
        autoComplete="name"
        disabled={isSubmitting}
      />

      <Input
        {...register('password')}
        type="password"
        label="Password"
        placeholder="At least 8 characters"
        error={errors.password?.message}
        autoComplete="new-password"
        disabled={isSubmitting}
      />

      <Input
        {...register('confirmPassword')}
        type="password"
        label="Confirm Password"
        placeholder="Re-enter your password"
        error={errors.confirmPassword?.message}
        autoComplete="new-password"
        disabled={isSubmitting}
      />

      <fieldset>
        <legend className="block text-sm font-medium text-gray-700 mb-3">
          I am a
        </legend>
        <div className="flex gap-6" role="group" aria-labelledby="role-legend">
          <label className="flex items-center cursor-pointer">
            <input
              type="radio"
              value="student"
              {...register('role')}
              className="h-4 w-4 text-blue-600 border-gray-300 focus:ring-blue-500"
              disabled={isSubmitting}
              aria-describedby="student-description"
            />
            <span className="ml-2 text-sm text-gray-700">
              <span className="font-medium">Student</span>
              <span id="student-description" className="block text-xs text-gray-500">Learn SQL through challenges</span>
            </span>
          </label>
          <label className="flex items-center cursor-pointer">
            <input
              type="radio"
              value="teacher"
              {...register('role')}
              className="h-4 w-4 text-blue-600 border-gray-300 focus:ring-blue-500"
              disabled={isSubmitting}
              aria-describedby="teacher-description"
            />
            <span className="ml-2 text-sm text-gray-700">
              <span className="font-medium">Teacher</span>
              <span id="teacher-description" className="block text-xs text-gray-500">Create and manage challenges</span>
            </span>
          </label>
        </div>
        {errors.role && (
          <p className="mt-1 text-sm text-red-600" role="alert">
            {errors.role.message}
          </p>
        )}
      </fieldset>

      <Button
        type="submit"
        variant="primary"
        size="lg"
        className="w-full"
        isLoading={isSubmitting}
        disabled={isSubmitting}
      >
        {isSubmitting ? 'Creating Account...' : 'Create Account'}
      </Button>
    </form>
  );
}
