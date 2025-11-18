import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import * as Sentry from '@sentry/react'
import './index.css'
import App from './App.tsx'

// Initialize Sentry for error tracking and performance monitoring
const sentryDsn = import.meta.env.VITE_SENTRY_DSN;
if (sentryDsn) {
  Sentry.init({
    dsn: sentryDsn,
    environment: import.meta.env.VITE_SENTRY_ENVIRONMENT || import.meta.env.VITE_ENV || 'development',

    // Performance Monitoring
    tracesSampleRate: parseFloat(import.meta.env.VITE_SENTRY_TRACES_SAMPLE_RATE || '0.1'),

    // Session Replay (helps debug errors by showing what user was doing)
    replaysSessionSampleRate: parseFloat(import.meta.env.VITE_SENTRY_REPLAYS_SESSION_SAMPLE_RATE || '0.1'),
    replaysOnErrorSampleRate: parseFloat(import.meta.env.VITE_SENTRY_REPLAYS_ERROR_SAMPLE_RATE || '1.0'),

    integrations: [
      // Browser tracing for performance monitoring
      Sentry.browserTracingIntegration({
        // Track all navigation and route changes
        enableInp: true,
      }),
      // Session replay for debugging
      Sentry.replayIntegration({
        maskAllText: false, // Set to true in production if dealing with sensitive data
        blockAllMedia: false,
      }),
    ],

    // Filter sensitive data before sending to Sentry
    beforeSend(event, hint) {
      // Don't send 401 errors (expected when tokens expire)
      if (event.exception?.values?.[0]?.value?.includes('401')) {
        return null;
      }

      // Filter sensitive data from breadcrumbs
      if (event.breadcrumbs) {
        event.breadcrumbs = event.breadcrumbs.map((breadcrumb) => {
          // Remove passwords, tokens from HTTP request data
          if (breadcrumb.data) {
            const filteredData = { ...breadcrumb.data };
            if (filteredData.password) filteredData.password = '[Filtered]';
            if (filteredData.token) filteredData.token = '[Filtered]';
            if (filteredData.refresh_token) filteredData.refresh_token = '[Filtered]';
            breadcrumb.data = filteredData;
          }
          return breadcrumb;
        });
      }

      return event;
    },
  });

  console.log(`Sentry initialized for environment: ${import.meta.env.VITE_ENV || 'development'}`);
} else {
  console.warn('VITE_SENTRY_DSN not set - error tracking disabled');
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <Sentry.ErrorBoundary
      fallback={({ error, resetError }) => (
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: '100vh',
          padding: '2rem',
          fontFamily: 'system-ui, sans-serif',
        }}>
          <div style={{
            maxWidth: '600px',
            textAlign: 'center',
            backgroundColor: '#fee',
            border: '1px solid #fcc',
            borderRadius: '8px',
            padding: '2rem',
          }}>
            <h1 style={{ fontSize: '2rem', marginBottom: '1rem', color: '#c00' }}>
              Oops! Something went wrong
            </h1>
            <p style={{ marginBottom: '1.5rem', color: '#666' }}>
              We've been notified and will investigate. You can try refreshing the page or going back to the homepage.
            </p>
            <details style={{ marginBottom: '1.5rem', textAlign: 'left' }}>
              <summary style={{ cursor: 'pointer', fontWeight: 'bold', marginBottom: '0.5rem' }}>
                Error Details
              </summary>
              <pre style={{
                backgroundColor: '#f5f5f5',
                padding: '1rem',
                borderRadius: '4px',
                overflow: 'auto',
                fontSize: '0.875rem',
              }}>
                {error.toString()}
              </pre>
            </details>
            <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center' }}>
              <button
                onClick={resetError}
                style={{
                  padding: '0.5rem 1rem',
                  backgroundColor: '#007bff',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  fontSize: '1rem',
                }}
              >
                Try Again
              </button>
              <button
                onClick={() => window.location.href = '/'}
                style={{
                  padding: '0.5rem 1rem',
                  backgroundColor: '#6c757d',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  fontSize: '1rem',
                }}
              >
                Go Home
              </button>
            </div>
          </div>
        </div>
      )}
      showDialog
    >
      <App />
    </Sentry.ErrorBoundary>
  </StrictMode>,
)
