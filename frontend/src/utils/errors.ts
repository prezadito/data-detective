import type { HTTPError, ValidationError, ApiErrorDetail } from '@/types';
import { HTTPError as KyHTTPError } from 'ky';

/**
 * Type guard to check if error is a ky HTTPError
 */
export function isHTTPError(error: unknown): error is HTTPError {
  return error instanceof KyHTTPError;
}

/**
 * Check if user is currently offline
 */
export function isOffline(): boolean {
  return !navigator.onLine;
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
    const networkKeywords = ['fetch', 'network', 'ECONNREFUSED', 'CORS', 'failed to fetch'];
    return networkKeywords.some(keyword =>
      error.message.toLowerCase().includes(keyword.toLowerCase())
    );
  }
  return false;
}

/**
 * Type guard to check if error is a timeout error
 */
export function isTimeoutError(error: unknown): boolean {
  if (error instanceof Error) {
    return error.name === 'TimeoutError' ||
           error.message.toLowerCase().includes('timeout') ||
           error.message.toLowerCase().includes('timed out');
  }
  return false;
}

/**
 * Error message mappings for common scenarios
 */
const ERROR_MESSAGES = {
  // Network errors
  OFFLINE: 'You appear to be offline. Please check your internet connection and try again.',
  NETWORK_ERROR: 'Unable to connect to the server. Please check your connection and try again.',
  TIMEOUT: 'The request took too long to complete. Please try again.',

  // Auth errors
  SESSION_EXPIRED: 'Your session has expired. Please log in again.',
  INVALID_CREDENTIALS: 'Invalid email or password. Please try again.',
  PERMISSION_DENIED: 'You do not have permission to perform this action.',

  // Generic errors
  NOT_FOUND: 'The requested information could not be found.',
  SERVER_ERROR: 'Something went wrong on our end. Please try again in a moment.',
  VALIDATION_ERROR: 'Please check your input and try again.',
  UNKNOWN_ERROR: 'An unexpected error occurred. Please try again.',
} as const;

/**
 * Parse API error response and extract user-friendly message
 */
export async function parseApiError(error: unknown): Promise<string> {
  // Check if user is offline first
  if (isOffline()) {
    return ERROR_MESSAGES.OFFLINE;
  }

  // Timeout errors
  if (isTimeoutError(error)) {
    return ERROR_MESSAGES.TIMEOUT;
  }

  // Network errors
  if (isNetworkError(error)) {
    return ERROR_MESSAGES.NETWORK_ERROR;
  }

  // HTTP errors from ky
  if (isHTTPError(error)) {
    try {
      const errorData = await error.response.json() as ApiErrorDetail;

      // Handle validation errors (array of errors)
      if (Array.isArray(errorData.detail)) {
        const validationErrors = errorData.detail as ValidationError[];
        if (validationErrors.length > 0) {
          // Return user-friendly validation error
          const firstError = validationErrors[0];
          const field = String(firstError.loc[firstError.loc.length - 1]);
          const fieldName = field.charAt(0).toUpperCase() + field.slice(1).replace(/_/g, ' ');
          return `${fieldName}: ${firstError.msg}`;
        }
        return ERROR_MESSAGES.VALIDATION_ERROR;
      }

      // Handle string error detail - make it more user-friendly
      if (typeof errorData.detail === 'string') {
        const detail = errorData.detail;

        // Map common backend error messages to user-friendly versions
        if (detail.toLowerCase().includes('invalid credentials') ||
            detail.toLowerCase().includes('incorrect password')) {
          return ERROR_MESSAGES.INVALID_CREDENTIALS;
        }
        if (detail.toLowerCase().includes('not found')) {
          return ERROR_MESSAGES.NOT_FOUND;
        }
        if (detail.toLowerCase().includes('already exists')) {
          return detail; // Keep the original message for duplicate entries
        }

        return detail;
      }
    } catch {
      // If JSON parsing fails, return generic message based on status
      const status = error.response.status;

      if (status === 401) {
        return ERROR_MESSAGES.SESSION_EXPIRED;
      }
      if (status === 403) {
        return ERROR_MESSAGES.PERMISSION_DENIED;
      }
      if (status === 404) {
        return ERROR_MESSAGES.NOT_FOUND;
      }
      if (status === 408) {
        return ERROR_MESSAGES.TIMEOUT;
      }
      if (status >= 500) {
        return ERROR_MESSAGES.SERVER_ERROR;
      }
      if (status >= 400) {
        return ERROR_MESSAGES.VALIDATION_ERROR;
      }

      return ERROR_MESSAGES.UNKNOWN_ERROR;
    }
  }

  // Standard Error object
  if (error instanceof Error) {
    // Don't show technical error messages to users
    if (error.message.includes('fetch') || error.message.includes('network')) {
      return ERROR_MESSAGES.NETWORK_ERROR;
    }
    return error.message;
  }

  // Unknown error type
  return ERROR_MESSAGES.UNKNOWN_ERROR;
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

/**
 * Check if an error is retryable
 * Returns true for network errors, timeouts, and 5xx server errors
 */
export function isRetryableError(error: unknown): boolean {
  // Network errors and timeouts are always retryable
  if (isNetworkError(error) || isTimeoutError(error)) {
    return true;
  }

  // HTTP errors - retry on server errors and some client errors
  if (isHTTPError(error)) {
    const status = error.response.status;
    // Retry on:
    // - 408 Request Timeout
    // - 429 Too Many Requests
    // - 500+ Server errors
    // - 503 Service Unavailable
    return status === 408 || status === 429 || status >= 500;
  }

  return false;
}
