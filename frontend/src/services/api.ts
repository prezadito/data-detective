import ky from 'ky';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

/**
 * Configured ky instance for API requests
 * - Automatic JSON parsing
 * - Timeout: 30 seconds
 * - Retry on network errors (3 attempts)
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
        // Handle 401 Unauthorized - clear token and redirect to login
        if (response.status === 401) {
          localStorage.removeItem('auth_token');
          // Could dispatch a logout action or redirect here
        }
        return response;
      },
    ],
  },
});

/**
 * Helper function to handle API errors
 */
export async function handleApiError(error: unknown): Promise<never> {
  if (error instanceof Error) {
    throw error;
  }
  throw new Error('An unexpected error occurred');
}
