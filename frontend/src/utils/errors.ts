import type { HTTPError, ValidationError, ApiErrorDetail } from '@/types';
import { HTTPError as KyHTTPError } from 'ky';

/**
 * Type guard to check if error is a ky HTTPError
 */
export function isHTTPError(error: unknown): error is HTTPError {
  return error instanceof KyHTTPError;
}

/**
 * Type guard to check if error is a network error
 */
export function isNetworkError(error: unknown): boolean {
  if (error instanceof Error) {
    // TypeError is thrown when network request fails (e.g., server not running)
    if (error.name === 'TypeError') {
      return true;
    }
    // Check error message for network-related keywords
    const networkKeywords = ['fetch', 'network', 'ECONNREFUSED', 'CORS'];
    return networkKeywords.some(keyword =>
      error.message.toLowerCase().includes(keyword.toLowerCase())
    );
  }
  return false;
}

/**
 * Parse API error response and extract user-friendly message
 */
export async function parseApiError(error: unknown): Promise<string> {
  // Network errors
  if (isNetworkError(error)) {
    return 'Cannot connect to server. Please ensure the backend is running at http://localhost:8000';
  }

  // HTTP errors from ky
  if (isHTTPError(error)) {
    try {
      const errorData = await error.response.json() as ApiErrorDetail;

      // Handle validation errors (array of errors)
      if (Array.isArray(errorData.detail)) {
        const validationErrors = errorData.detail as ValidationError[];
        if (validationErrors.length > 0) {
          // Return first validation error message
          const firstError = validationErrors[0];
          const field = firstError.loc[firstError.loc.length - 1];
          return `${field}: ${firstError.msg}`;
        }
      }

      // Handle string error detail
      if (typeof errorData.detail === 'string') {
        return errorData.detail;
      }
    } catch {
      // If JSON parsing fails, return generic message based on status
      const status = error.response.status;

      if (status === 401) {
        return 'Your session has expired. Please log in again.';
      }
      if (status === 403) {
        return 'You do not have permission to perform this action.';
      }
      if (status === 404) {
        return 'The requested resource was not found.';
      }
      if (status >= 500) {
        return 'Server error. Please try again later.';
      }

      return 'An error occurred. Please try again.';
    }
  }

  // Standard Error object
  if (error instanceof Error) {
    return error.message;
  }

  // Unknown error type
  return 'An unexpected error occurred. Please try again.';
}

/**
 * Extract validation errors from API response
 * Returns a map of field names to error messages
 */
export async function extractValidationErrors(
  error: unknown
): Promise<Record<string, string>> {
  if (!isHTTPError(error)) {
    return {};
  }

  try {
    const errorData = await error.response.json() as ApiErrorDetail;

    if (Array.isArray(errorData.detail)) {
      const validationErrors = errorData.detail as ValidationError[];
      const errorMap: Record<string, string> = {};

      for (const validationError of validationErrors) {
        // Get the field name (last item in loc array)
        const field = validationError.loc[validationError.loc.length - 1];
        errorMap[field] = validationError.msg;
      }

      return errorMap;
    }
  } catch {
    // Ignore JSON parsing errors
  }

  return {};
}

/**
 * Get HTTP status code from error
 */
export function getErrorStatus(error: unknown): number | null {
  if (isHTTPError(error)) {
    return error.response.status;
  }
  return null;
}

/**
 * Check if error is a specific HTTP status
 */
export function isErrorStatus(error: unknown, status: number): boolean {
  return getErrorStatus(error) === status;
}
