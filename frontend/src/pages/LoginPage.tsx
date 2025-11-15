import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { LoginForm } from '@/components/auth/LoginForm';

export function LoginPage() {
  const navigate = useNavigate();
  const { isAuthenticated, isLoading } = useAuth();

  // Redirect to dashboard if already authenticated
  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      navigate('/dashboard', { replace: true });
    }
  }, [isAuthenticated, isLoading, navigate]);

  // Show loading state while checking authentication
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600" />
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div className="text-center">
          <h1 className="text-4xl font-bold text-gray-900">Data Detective</h1>
          <h2 className="mt-6 text-3xl font-extrabold text-gray-900">
            Sign in to your account
          </h2>
          <p className="mt-2 text-sm text-gray-600">
            Master SQL through interactive challenges
          </p>
        </div>

        <div className="mt-8 bg-white py-8 px-4 shadow-lg rounded-lg sm:px-10">
          <LoginForm />
        </div>

        <div className="text-center">
          <p className="text-sm text-gray-600">
            Don't have an account?{' '}
            <a
              href="/register"
              className="font-medium text-blue-600 hover:text-blue-500 focus:outline-none focus:underline transition"
            >
              Sign up
            </a>
          </p>
        </div>
      </div>
    </div>
  );
}
