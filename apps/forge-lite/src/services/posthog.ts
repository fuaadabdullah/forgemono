// PostHog Analytics Service
import PostHog from 'posthog-react-native';
import Constants from 'expo-constants';

// PostHog instance
let posthogInstance: PostHog | null = null;

const initializePostHog = async () => {
  if (posthogInstance) return posthogInstance;

  const apiKey = Constants.expoConfig?.extra?.posthogApiKey || process.env.EXPO_PUBLIC_POSTHOG_API_KEY;
  const host = Constants.expoConfig?.extra?.posthogHost || process.env.EXPO_PUBLIC_POSTHOG_HOST;
  const supportEmail = (Constants.expoConfig as any)?.extra?.supportEmail ||
    process.env.EXPO_PUBLIC_SUPPORT_EMAIL ||
    'goblinosrep@gmail.com';

  if (!apiKey || !host) {
    console.warn('PostHog API key or host not found. Analytics disabled.');
    return null;
  }

  try {
    posthogInstance = new PostHog(apiKey, {
      host,
      // Disable in development unless explicitly enabled
      disabled: __DEV__ && !process.env.FORCE_ANALYTICS,
      // Capture app lifecycle events
      captureAppLifecycleEvents: true,
      // Capture deep links
      // Note: deep links capture might be configured differently
      // flush interval
      flushAt: 20,
      // Max queue size
      maxQueueSize: 1000,
    });

    await posthogInstance.ready();
    // Register app-wide super properties for triage/attribution
    try {
      await posthogInstance.register({ app_support_email: supportEmail });
    } catch {}
    console.log('PostHog initialized successfully');
    return posthogInstance;
  } catch (error) {
    console.error('Failed to initialize PostHog:', error);
    return null;
  }
};

// Analytics helper functions
export const analytics = {
  // Initialize analytics (call this on app start)
  init: initializePostHog,

  // Identify user (only if they consent to analytics)
  identify: async (userId: string, properties?: Record<string, any>) => {
    if (!posthogInstance) return;

    try {
      const supportEmail = (Constants.expoConfig as any)?.extra?.supportEmail ||
        process.env.EXPO_PUBLIC_SUPPORT_EMAIL ||
        'goblinosrep@gmail.com';
      posthogInstance.identify(userId, { app_support_email: supportEmail, ...(properties || {}) });
      if (__DEV__) {
        console.log('Analytics: identify', userId, properties);
      }
    } catch (error) {
      console.error('Analytics identify error:', error);
    }
  },

  // Track events
  track: async (event: string, properties?: Record<string, any>) => {
    if (!posthogInstance) return;

    try {
      await posthogInstance.capture(event, properties);
      if (__DEV__) {
        console.log('Analytics: track', event, properties);
      }
    } catch (error) {
      console.error('Analytics track error:', error);
    }
  },

  // Track screen views
  screen: async (screenName: string, properties?: Record<string, any>) => {
    if (!posthogInstance) return;

    try {
      await posthogInstance.screen(screenName, properties);
      if (__DEV__) {
        console.log('Analytics: screen', screenName, properties);
      }
    } catch (error) {
      console.error('Analytics screen error:', error);
    }
  },

  // Reset user when they log out
  reset: () => {
    if (!posthogInstance) return;

    try {
      posthogInstance.reset();
      if (__DEV__) {
        console.log('Analytics: reset');
      }
    } catch (error) {
      console.error('Analytics reset error:', error);
    }
  },

  // Enable/disable analytics based on user consent
  setEnabled: async (enabled: boolean) => {
    if (!posthogInstance) return;

    try {
      if (enabled) {
        await posthogInstance.optIn();
      } else {
        await posthogInstance.optOut();
      }
      if (__DEV__) {
        console.log('Analytics: setEnabled', enabled);
      }
    } catch (error) {
      console.error('Analytics setEnabled error:', error);
    }
  },

  // Flush pending events
  flush: async () => {
    if (!posthogInstance) return;

    try {
      await posthogInstance.flush();
      if (__DEV__) {
        console.log('Analytics: flush');
      }
    } catch (error) {
      console.error('Analytics flush error:', error);
    }
  },

  // Check if analytics is enabled
  isEnabled: () => {
    return posthogInstance !== null;
  }
};

// Predefined tracking events for ForgeTM Lite
export const trackingEvents = {
  // Authentication
  SIGN_UP: 'user_signed_up',
  SIGN_IN: 'user_signed_in',
  SIGN_OUT: 'user_signed_out',

  // Trading
  TRADE_CREATED: 'trade_created',
  TRADE_UPDATED: 'trade_updated',
  TRADE_CLOSED: 'trade_closed',
  TRADE_DELETED: 'trade_deleted',

  // Watchlists
  WATCHLIST_CREATED: 'watchlist_created',
  WATCHLIST_UPDATED: 'watchlist_updated',
  WATCHLIST_DELETED: 'watchlist_deleted',

  // Journal
  JOURNAL_ENTRY_CREATED: 'journal_entry_created',
  JOURNAL_ENTRY_UPDATED: 'journal_entry_updated',

  // App Usage
  APP_OPENED: 'app_opened',
  APP_CLOSED: 'app_closed',
  SCREEN_VIEW: 'screen_view',

  // Features
  MARKET_DATA_FETCHED: 'market_data_fetched',
  RISK_CALCULATION_USED: 'risk_calculation_used',
  EXPORT_DATA: 'data_exported',

  // Feedback
  FEEDBACK_SUBMITTED: 'feedback_submitted',
  RATING_GIVEN: 'rating_given',
} as const;

// Export PostHog instance for advanced usage
export { PostHog };
