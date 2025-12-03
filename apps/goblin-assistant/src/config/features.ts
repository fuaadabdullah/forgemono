/**
 * Feature flags configuration
 * Controls which features are enabled in the application
 */

export interface FeatureFlags {
  ragEnabled: boolean;
  multiProvider: boolean;
  passkeyAuth: boolean;
  googleAuth: boolean;
  orchestration: boolean;
  sandbox: boolean;
  analytics: boolean;
  debugMode: boolean;
}

// Load from environment variables with sensible defaults
export const featureFlags: FeatureFlags = {
  ragEnabled: import.meta.env.VITE_FEATURE_RAG_ENABLED === 'true',
  multiProvider: import.meta.env.VITE_FEATURE_MULTI_PROVIDER === 'true',
  passkeyAuth: import.meta.env.VITE_FEATURE_PASSKEY_AUTH === 'true',
  googleAuth: import.meta.env.VITE_FEATURE_GOOGLE_AUTH === 'true',
  orchestration: import.meta.env.VITE_FEATURE_ORCHESTRATION === 'true',
  sandbox: import.meta.env.VITE_FEATURE_SANDBOX === 'true',
  analytics: import.meta.env.VITE_ENABLE_ANALYTICS === 'true',
  debugMode: import.meta.env.VITE_DEBUG_MODE === 'true',
};

// Helper function to check if a feature is enabled
export const isFeatureEnabled = (feature: keyof FeatureFlags): boolean => {
  return featureFlags[feature];
};

// Log enabled features in development
if (featureFlags.debugMode) {
  console.log('🚩 Feature Flags:', featureFlags);
}
