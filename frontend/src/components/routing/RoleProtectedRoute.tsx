import { Navigate } from 'react-router-dom';
import type { ReactNode } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import type { UserRole } from '@/types';

interface RoleProtectedRouteProps {
  children: ReactNode;
  requiredRole: UserRole;
}

/**
 * Protected route wrapper that requires authentication and specific role
 * Redirects to /login if user is not authenticated
 * Redirects to /practice if user doesn't have the required role
 */
export function RoleProtectedRoute({ children, requiredRole }: RoleProtectedRouteProps) {
  const { isAuthenticated, isLoading, user } = useAuth();

  // Show loading spinner while checking authentication state
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600" />
      </div>
    );
  }

  // Redirect to login if not authenticated
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  // Redirect to practice if user doesn't have the required role
  if (user?.role !== requiredRole) {
    return <Navigate to="/practice" replace />;
  }

  // Render protected content
  return <>{children}</>;
}
