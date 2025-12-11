import * as Sentry from '@sentry/browser';

// Initialize Sentry with Datadog intake
Sentry.init({
  dsn: "https://c751f8c0875fd4e2561e0b0821d4da89@sentry-intake.datadoghq.com/1",
  environment: import.meta.env.VITE_DD_ENV || 'development',
  tracesSampleRate: 1.0,
  // Capture console errors and unhandled promise rejections
  beforeSend(event) {
    // Add service tag for Datadog
    event.tags = {
      ...event.tags,
      service: 'GoblinOS Assistant'
    };

    // Add environment info
    event.tags = {
      ...event.tags,
      environment: import.meta.env.VITE_DD_ENV || 'development'
    };

    return event;
  },
});

// Set the service tag globally
Sentry.setTag('service', 'GoblinOS Assistant');

// Set user context if available
const setUserContext = (user: { id?: string; email?: string; name?: string }) => {
  Sentry.setUser({
    id: user.id,
    email: user.email,
    username: user.name,
  });
};

// Error tracking utilities
export const sentryErrorTracking = {
  captureException: (error: Error, context?: Record<string, unknown>) => {
    if (context) {
      Sentry.withScope((scope) => {
        Object.keys(context).forEach(key => {
          scope.setTag(key, String(context[key]));
        });
        Sentry.captureException(error);
      });
    } else {
      Sentry.captureException(error);
    }
  },

  captureMessage: (message: string, level: 'fatal' | 'error' | 'warning' | 'info' | 'debug' = 'error', context?: Record<string, unknown>) => {
    if (context) {
      Sentry.withScope((scope) => {
        Object.keys(context).forEach(key => {
          scope.setTag(key, String(context[key]));
        });
        Sentry.captureMessage(message, level);
      });
    } else {
      Sentry.captureMessage(message, level);
    }
  },

  setUser: setUserContext,

  addBreadcrumb: (message: string, category?: string, level?: 'fatal' | 'error' | 'warning' | 'info' | 'debug') => {
    Sentry.addBreadcrumb({
      message,
      category: category || 'custom',
      level: level || 'info',
    });
  },

  setContext: (key: string, context: Record<string, unknown>) => {
    Sentry.setContext(key, context);
  },
};

export default Sentry;
