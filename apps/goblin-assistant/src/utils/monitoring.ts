// src/utils/monitoring.ts - Error monitoring with Sentry integration
import * as Sentry from '@sentry/react';
import { env } from '../config/env';

const sentry: any = Sentry;

interface ErrorContext {
  componentStack?: string;
  [key: string]: unknown;
}

// Initialize Sentry if DSN is provided
if (typeof window !== 'undefined' && env.isProduction && env.sentryDsn) {
  sentry.init({
    dsn: env.sentryDsn,
    environment: env.mode,
    integrations: [
      sentry.browserTracingIntegration(),
      sentry.replayIntegration({
        maskAllText: true,
        blockAllMedia: true,
      }),
    ],
    // Performance Monitoring
    tracesSampleRate: 1.0, // Capture 100% of the transactions
    // Session Replay
    replaysSessionSampleRate: 0.1, // This sets the sample rate at 10%. You may want to change it to 100% while in development and then sample at a lower rate in production.
    replaysOnErrorSampleRate: 1.0, // If you're not already sampling the entire session, change the sample rate to 100% when sampling sessions where errors occur.
  });
}

export function logErrorToService(error: Error, context?: ErrorContext) {
  if (env.isProduction && typeof window !== 'undefined') {
    // Send to Sentry if configured
    if (env.sentryDsn) {
      sentry.captureException(error, {
        contexts: context ? { react: context } : undefined,
        tags: {
          component: 'frontend',
          environment: env.mode,
        },
      });
    }

    // Fallback: Send to custom endpoint
    fetch('/api/errors', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: error.message,
        stack: error.stack,
        context,
        timestamp: new Date().toISOString(),
        userAgent: navigator.userAgent,
        url: window.location.href,
      }),
    }).catch(() => {
      // Silent fail - don't break app if logging fails
    });
  } else {
    console.error('Error logged:', error, context);
  }
}

// Helper to convert React ErrorInfo to our ErrorContext
export function reactErrorInfoToContext(errorInfo: React.ErrorInfo): ErrorContext {
  return {
    componentStack: errorInfo.componentStack || undefined,
  };
}

// Performance monitoring helper
export function logPerformanceMetric(name: string, value: number) {
  if (env.isProduction && env.sentryDsn && typeof window !== 'undefined') {
    // Log performance metrics to Sentry using setMeasurement
    sentry.setMeasurement(name, value, 'none');
  }
}
