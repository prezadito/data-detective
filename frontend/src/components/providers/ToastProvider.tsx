import { Toaster } from 'sonner';
import type { ReactNode } from 'react';

interface ToastProviderProps {
  children: ReactNode;
}

/**
 * Toast notification provider using Sonner
 * Wraps the app to enable toast notifications
 */
export function ToastProvider({ children }: ToastProviderProps) {
  return (
    <>
      {children}
      <Toaster
        position="top-right"
        expand={false}
        richColors
        closeButton
        toastOptions={{
          className: 'font-sans',
          duration: 4000,
          style: {
            background: 'white',
            color: '#0f172a',
            border: '1px solid #e2e8f0',
          },
        }}
      />
    </>
  );
}
