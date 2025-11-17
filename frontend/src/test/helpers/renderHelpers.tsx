/**
 * Custom render helpers for testing React components
 * Provides consistent setup for different testing scenarios
 */

import { render, type RenderOptions } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { AuthProvider } from '@/contexts/AuthContext';
import { DatabaseProvider } from '@/contexts/DatabaseContext';
import type { User } from '@/types';

interface RenderWithRouterOptions extends RenderOptions {
  route?: string;
}

/**
 * Render component with Router wrapper
 * Use for components that use useNavigate or Link
 */
export function renderWithRouter(
  ui: React.ReactElement,
  { route = '/', ...options }: RenderWithRouterOptions = {}
) {
  window.history.pushState({}, 'Test page', route);

  return render(ui, {
    wrapper: ({ children }) => <BrowserRouter>{children}</BrowserRouter>,
    ...options,
  });
}

interface RenderWithAuthOptions extends RenderOptions {
  user?: User | null;
  isAuthenticated?: boolean;
  route?: string;
}

/**
 * Render component with mocked AuthContext
 * NOTE: This requires vi.mock('@/contexts/AuthContext') to be set up in the test file
 * Use for components that use useAuth hook
 */
export function renderWithAuth(
  ui: React.ReactElement,
  {
    route = '/',
    ...options
  }: RenderWithAuthOptions = {}
) {
  window.history.pushState({}, 'Test page', route);

  return render(ui, {
    wrapper: ({ children }) => <BrowserRouter>{children}</BrowserRouter>,
    ...options,
  });
}

interface RenderWithProvidersOptions extends RenderOptions {
  route?: string;
}

/**
 * Render component with all providers (Router + Auth + Database)
 * Use for integration tests or components that need multiple contexts
 * NOTE: This requires mocking AuthContext and DatabaseContext in the test file
 */
export function renderWithProviders(
  ui: React.ReactElement,
  { route = '/', ...options }: RenderWithProvidersOptions = {}
) {
  window.history.pushState({}, 'Test page', route);

  return render(
    <BrowserRouter>
      <DatabaseProvider>
        <AuthProvider>{ui}</AuthProvider>
      </DatabaseProvider>
    </BrowserRouter>,
    options
  );
}
