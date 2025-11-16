import { useState, useCallback } from 'react';
import { showSuccessToast, showApiErrorToast } from '@/utils/toast';

interface UseApiOptions<T> {
  /**
   * Callback to run on successful API call
   */
  onSuccess?: (data: T) => void;

  /**
   * Callback to run on API error
   */
  onError?: (error: unknown) => void;

  /**
   * Success message to show in toast
   */
  successMessage?: string;

  /**
   * Whether to show error toast on error (default: true)
   */
  showErrorToast?: boolean;
}

interface UseApiReturn<T, TArgs extends unknown[]> {
  /**
   * Response data from the API call
   */
  data: T | null;

  /**
   * Error from the API call
   */
  error: unknown | null;

  /**
   * Loading state
   */
  isLoading: boolean;

  /**
   * Execute the API call
   */
  execute: (...args: TArgs) => Promise<T | null>;

  /**
   * Reset the state
   */
  reset: () => void;
}

/**
 * Hook for making API calls with automatic loading and error handling
 *
 * @example
 * ```tsx
 * const { isLoading, execute } = useApi(authService.login, {
 *   successMessage: 'Logged in successfully!',
 *   onSuccess: () => navigate('/dashboard')
 * });
 *
 * await execute(credentials);
 * ```
 */
export function useApi<T, TArgs extends unknown[]>(
  apiFunction: (...args: TArgs) => Promise<T>,
  options: UseApiOptions<T> = {}
): UseApiReturn<T, TArgs> {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<unknown | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const {
    onSuccess,
    onError,
    successMessage,
    showErrorToast: shouldShowErrorToast = true,
  } = options;

  const execute = useCallback(
    async (...args: TArgs): Promise<T | null> => {
      try {
        setIsLoading(true);
        setError(null);

        const result = await apiFunction(...args);
        setData(result);

        // Show success message if provided
        if (successMessage) {
          showSuccessToast(successMessage);
        }

        // Call success callback
        if (onSuccess) {
          onSuccess(result);
        }

        return result;
      } catch (err) {
        setError(err);

        // Show error toast
        if (shouldShowErrorToast) {
          await showApiErrorToast(err);
        }

        // Call error callback
        if (onError) {
          onError(err);
        }

        return null;
      } finally {
        setIsLoading(false);
      }
    },
    [apiFunction, onSuccess, onError, successMessage, shouldShowErrorToast]
  );

  const reset = useCallback(() => {
    setData(null);
    setError(null);
    setIsLoading(false);
  }, []);

  return {
    data,
    error,
    isLoading,
    execute,
    reset,
  };
}
