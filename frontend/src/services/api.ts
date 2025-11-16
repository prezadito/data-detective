import ky from 'ky';
import { showErrorToast } from '@/utils/toast';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

/**
 * Configured ky instance for API requests
 * - Automatic JSON parsing
 * - Timeout: 30 seconds
 * - Retry on network errors (3 attempts)
 * - Automatic 401/403 handling
 */
export const api = ky.create({
  prefixUrl: API_BASE_URL,
  timeout: 30000,
  retry: {
    limit: 3,
    statusCodes: [408, 413, 429, 500, 502, 503, 504],
  },
  hooks: {
    beforeRequest: [
      (request) => {
        // Add auth token if available
        const token = localStorage.getItem('auth_token');
        if (token) {
          request.headers.set('Authorization', `Bearer ${token}`);
        }
      },
    ],
    afterResponse: [
      async (_request, _options, response) => {
        // Handle 401 Unauthorized - clear tokens and redirect to login
        if (response.status === 401) {
          // Clear auth tokens
          localStorage.removeItem('auth_token');
          localStorage.removeItem('refresh_token');

          // Show toast notification
          showErrorToast('Your session has expired. Please log in again.');

          // Redirect to login page (only if not already there)
          if (!window.location.pathname.includes('/login')) {
            window.location.href = '/login';
          }
        }

        // Handle 403 Forbidden - show permission error
        if (response.status === 403) {
          showErrorToast('You do not have permission to perform this action.');
        }

        return response;
      },
    ],
  },
});
