import ky from 'ky';
import { showErrorToast } from '@/utils/toast';
import { isOffline } from '@/utils/errors';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

/**
 * Calculate exponential backoff delay
 * @param attemptCount - Current retry attempt (0-indexed)
 * @returns Delay in milliseconds
 */
function getRetryDelay(attemptCount: number): number {
  // Exponential backoff: 1s, 2s, 4s, 8s
  const baseDelay = 1000;
  const delay = baseDelay * Math.pow(2, attemptCount);
  // Add jitter (random 0-500ms) to prevent thundering herd
  const jitter = Math.random() * 500;
  return delay + jitter;
}

/**
 * Configured ky instance for API requests
 * - Automatic JSON parsing
 * - Timeout: 30 seconds
 * - Retry with exponential backoff (up to 4 attempts)
 * - Automatic 401/403 handling
 * - Offline detection
 */
export const api = ky.create({
  prefixUrl: API_BASE_URL,
  timeout: 30000,
  retry: {
    limit: 3, // Will retry up to 3 times (4 total attempts)
    methods: ['get', 'post', 'put', 'delete', 'patch'],
    statusCodes: [408, 413, 429, 500, 502, 503, 504],
    backoffLimit: 16000, // Maximum delay between retries
    delay: getRetryDelay,
  },
  hooks: {
    beforeRequest: [
      (request) => {
        // Check if user is offline before making request
        if (isOffline()) {
          throw new Error('You appear to be offline. Please check your internet connection.');
        }

        // Add auth token if available
        const token = localStorage.getItem('auth_token');
        if (token) {
          request.headers.set('Authorization', `Bearer ${token}`);
        }
      },
    ],
    beforeRetry: [
      ({ request, error, retryCount }) => {
        console.log(`Retrying request to ${request.url} (attempt ${retryCount + 1})`, error);

        // Check if still offline before retry
        if (isOffline()) {
          throw new Error('You appear to be offline. Please check your internet connection.');
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
