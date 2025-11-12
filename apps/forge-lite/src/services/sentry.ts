import * as Sentry from '@sentry/react-native';
import Constants from 'expo-constants';

// Initialize Sentry
const initializeSentry = () => {
  const dsn = Constants.expoConfig?.extra?.sentryDsn || process.env.EXPO_PUBLIC_SENTRY_DSN;
  const supportEmail =
    (Constants.expoConfig as any)?.extra?.supportEmail ||
    process.env.EXPO_PUBLIC_SUPPORT_EMAIL ||
    'goblinosrep@gmail.com';

  if (!dsn) {
    console.warn('Sentry DSN not found. Crash reporting disabled.');
    return;
  }

  Sentry.init({
    dsn,
    debug: __DEV__,
    environment: process.env.NODE_ENV || 'development',
    // Only enable crash reporting if user has consented
    enabled: true, // This should be controlled by user preferences
    // Performance monitoring
    tracesSampleRate: __DEV__ ? 1.0 : 0.1,
    // Release tracking
    release: Constants.expoConfig?.version,
    // User context (will be set when user logs in)
    beforeSend: (event) => {
      // Remove sensitive data
      if (event.user) {
        delete event.user.email;
        delete event.user.ip_address;
      }
      // Attach support contact info as tag and extra for triage
      event.tags = { ...(event.tags || {}), support_email: supportEmail };
      event.extra = { ...(event.extra || {}), support_email: supportEmail };
      return event;
    },
  });

  // Also set on scope for non-error breadcrumb contexts
  Sentry.setTag('support_email', supportEmail);
  Sentry.setContext('support', { email: supportEmail });
};

// Set user context for Sentry
export const setSentryUser = (userId: string, email?: string) => {
  Sentry.setUser({
    id: userId,
    // Only include email if user has consented to analytics
    ...(email && { email }),
  });
};

// Clear user context
export const clearSentryUser = () => {
  Sentry.setUser(null);
};

// Capture exceptions
export const captureException = (error: Error, context?: Record<string, any>) => {
  Sentry.captureException(error, {
    tags: {
      component: 'app',
    },
    extra: context,
  });
};

// Capture messages
export const captureMessage = (message: string, level: Sentry.SeverityLevel = 'info') => {
  Sentry.captureMessage(message, level);
};

// Performance monitoring
export const startSpan = (name: string, op: string) => {
  return Sentry.startSpan({
    name,
    op,
  }, () => {});
};

export default initializeSentry;
