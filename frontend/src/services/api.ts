import ky from 'ky';
import * as Sentry from '@sentry/react';
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

        // Add breadcrumb to Sentry for all API requests
        Sentry.addBreadcrumb({
          category: 'api',
          message: `API Request: ${request.method} ${request.url}`,
          level: 'info',
          data: {
            method: request.method,
            url: request.url,
          },
        });
      },
    ],
    beforeRetry: [
      ({ request, error, retryCount }) => {
        console.log(`Retrying request to ${request.url} (attempt ${retryCount + 1})`, error);

        // Add breadcrumb for retry
        Sentry.addBreadcrumb({
          category: 'api',
          message: `API Retry: ${request.method} ${request.url} (attempt ${retryCount + 1})`,
          level: 'warning',
          data: {
            method: request.method,
            url: request.url,
            retryCount: retryCount + 1,
            error: error.message,
          },
        });

        // Check if still offline before retry
        if (isOffline()) {
          throw new Error('You appear to be offline. Please check your internet connection.');
        }
      },
    ],
    afterResponse: [
      async (request, _options, response) => {
        // Add breadcrumb for response
        Sentry.addBreadcrumb({
          category: 'api',
          message: `API Response: ${request.method} ${request.url} - ${response.status}`,
          level: response.status >= 400 ? 'error' : 'info',
          data: {
            method: request.method,
            url: request.url,
            status: response.status,
            statusText: response.statusText,
          },
        });

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

          // Don't capture 401 in Sentry (expected behavior)
          return response;
        }

        // Handle 403 Forbidden - show permission error
        if (response.status === 403) {
          showErrorToast('You do not have permission to perform this action.');

          // Capture permission errors in Sentry with context
          Sentry.captureMessage('Permission Denied', {
            level: 'warning',
            tags: {
              http_status: '403',
              endpoint: request.url,
            },
            extra: {
              method: request.method,
              url: request.url,
            },
          });
        }

        // Capture 5xx server errors in Sentry
        if (response.status >= 500) {
          Sentry.captureMessage(`Server Error: ${response.status} ${response.statusText}`, {
            level: 'error',
            tags: {
              http_status: response.status.toString(),
              endpoint: request.url,
            },
            extra: {
              method: request.method,
              url: request.url,
              status: response.status,
              statusText: response.statusText,
            },
          });
        }

        // Capture 4xx client errors (except 401) in Sentry
        if (response.status >= 400 && response.status < 500 && response.status !== 401) {
          Sentry.captureMessage(`Client Error: ${response.status} ${response.statusText}`, {
            level: 'warning',
            tags: {
              http_status: response.status.toString(),
              endpoint: request.url,
            },
            extra: {
              method: request.method,
              url: request.url,
              status: response.status,
              statusText: response.statusText,
            },
          });
        }

        return response;
      },
    ],
  },
});
