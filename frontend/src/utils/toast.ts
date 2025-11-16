import { toast } from 'sonner';
import { parseApiError } from './errors';

/**
 * Show success toast notification
 */
export function showSuccessToast(message: string): void {
  toast.success(message);
}

/**
 * Show error toast notification
 */
export function showErrorToast(message: string): void {
  toast.error(message);
}

/**
 * Show info toast notification
 */
export function showInfoToast(message: string): void {
  toast.info(message);
}

/**
 * Show warning toast notification
 */
export function showWarningToast(message: string): void {
  toast.warning(message);
}

/**
 * Show error toast from API error
 * Automatically parses the error and shows appropriate message
 */
export async function showApiErrorToast(error: unknown): Promise<void> {
  const errorMessage = await parseApiError(error);
  showErrorToast(errorMessage);
}

/**
 * Show loading toast with promise
 * Automatically shows success/error based on promise resolution
 */
export function showPromiseToast<T>(
  promise: Promise<T>,
  options: {
    loading: string;
    success: string | ((data: T) => string);
    error: string | ((error: unknown) => string);
  }
): void {
  toast.promise(promise, {
    loading: options.loading,
    success: (data) => {
      if (typeof options.success === 'function') {
        return options.success(data);
      }
      return options.success;
    },
    error: (error) => {
      if (typeof options.error === 'function') {
        return options.error(error);
      }
      return options.error;
    },
  });
}
