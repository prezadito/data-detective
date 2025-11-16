import { Component, type ReactNode } from 'react';
import { Button } from './Button';

interface ErrorBoundaryProps {
  children: ReactNode;
  /**
   * Optional fallback UI to render when error occurs
   */
  fallback?: (error: Error, reset: () => void) => ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

/**
 * Error boundary component to catch React rendering errors
 * Displays a user-friendly fallback UI when errors occur
 */
export class ErrorBoundary extends Component<
  ErrorBoundaryProps,
  ErrorBoundaryState
> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
    };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    // Update state so the next render will show the fallback UI
    return {
      hasError: true,
      error,
    };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo): void {
    // Log error to console for debugging
    console.error('ErrorBoundary caught an error:', error, errorInfo);

    // In production, you might want to log this to an error reporting service
    // Example: Sentry.captureException(error, { extra: errorInfo });
  }

  resetError = (): void => {
    this.setState({
      hasError: false,
      error: null,
    });
  };

  render(): ReactNode {
    if (this.state.hasError && this.state.error) {
      // Use custom fallback if provided
      if (this.props.fallback) {
        return this.props.fallback(this.state.error, this.resetError);
      }

      // Default fallback UI
      return (
        <div
          className="min-h-screen flex items-center justify-center bg-gray-50 px-4"
          role="alert"
          aria-live="assertive"
        >
          <div className="max-w-md w-full bg-white rounded-lg shadow-lg p-6">
            <div className="flex items-center justify-center w-12 h-12 mx-auto bg-red-100 rounded-full">
              <svg
                className="w-6 h-6 text-red-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
                aria-hidden="true"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                />
              </svg>
            </div>

            <h1 className="mt-4 text-xl font-bold text-center text-gray-900">
              Something went wrong
            </h1>

            <p className="mt-2 text-sm text-center text-gray-600">
              We&apos;re sorry, but something unexpected happened. Please try again.
            </p>

            {import.meta.env.MODE === 'development' && this.state.error && (
              <div className="mt-4 p-4 bg-gray-100 rounded-md">
                <p className="text-xs font-mono text-red-600">
                  {this.state.error.toString()}
                </p>
                {this.state.error.stack && (
                  <pre className="mt-2 text-xs font-mono text-gray-700 overflow-auto max-h-32">
                    {this.state.error.stack}
                  </pre>
                )}
              </div>
            )}

            <div className="mt-6 flex gap-3">
              <Button
                onClick={this.resetError}
                variant="primary"
                className="flex-1"
              >
                Try Again
              </Button>
              <Button
                onClick={() => (window.location.href = '/')}
                variant="outline"
                className="flex-1"
              >
                Go Home
              </Button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
