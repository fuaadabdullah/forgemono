/**
 * Centralized environment configuration
 *
 * Benefits:
 * - Type safety for env vars
 * - Validation at startup
 * - Single source of truth
 * - Easier testing
 */

import { devLog } from '../utils/dev-log';

interface EnvConfig {
  // API Configuration
  apiBaseUrl: string;
  backendUrl: string;
  fastApiUrl: string;

  // Feature Flags
  enableDebug: boolean;
  mockApi: boolean;
  features: {
    ragEnabled: boolean;
    multiProvider: boolean;
    passkeyAuth: boolean;
    googleAuth: boolean;
    orchestration: boolean;
    sandbox: boolean;
    analytics: boolean;
    debugMode: boolean;
  };

  // Turnstile
  turnstile: {
    chat: string;
    login: string;
    search: string;
  };

  // Monitoring
  sentryDsn: string;
  posthogApiKey: string;
  posthogHost: string;

  // Build Info
  mode: 'development' | 'production' | 'test';
  isDevelopment: boolean;
  isProduction: boolean;
}

function getRequiredEnv(key: string): string {
  const value = import.meta.env[key];
  if (!value) {
    throw new Error(`Missing required environment variable: ${key}`);
  }
  return value;
}

function getOptionalEnv(key: string, defaultValue: string = ''): string {
  return import.meta.env[key] || defaultValue;
}

function validateEnvConfig(config: EnvConfig): void {
  const errors: string[] = [];

  // Validate URLs
  try {
    new URL(config.apiBaseUrl);
  } catch {
    errors.push(`Invalid VITE_API_BASE_URL: ${config.apiBaseUrl}`);
  }

  // Warn about production mode with debug enabled
  if (config.isProduction && config.enableDebug) {
    console.warn('⚠️  Debug mode enabled in production!');
  }

  // Check Turnstile keys format
  Object.entries(config.turnstile).forEach(([key, value]) => {
    if (value && !value.startsWith('0x')) {
      errors.push(`Invalid Turnstile key format for ${key}`);
    }
  });

  if (errors.length > 0) {
    console.error('❌ Environment configuration errors:\n', errors.join('\n'));
    throw new Error('Invalid environment configuration');
  }
}

// Export typed configuration
export const env: EnvConfig = {
  apiBaseUrl: getRequiredEnv('VITE_API_BASE_URL'),
  backendUrl: getOptionalEnv('VITE_BACKEND_URL', 'http://localhost:8000'),
  fastApiUrl: getOptionalEnv('VITE_FASTAPI_URL', 'http://localhost:8001'),

  enableDebug: getOptionalEnv('VITE_ENABLE_DEBUG') === 'true',
  mockApi: getOptionalEnv('VITE_MOCK_API') === 'true',

  features: {
    ragEnabled: getOptionalEnv('VITE_FEATURE_RAG_ENABLED') === 'true',
    multiProvider: getOptionalEnv('VITE_FEATURE_MULTI_PROVIDER') === 'true',
    passkeyAuth: getOptionalEnv('VITE_FEATURE_PASSKEY_AUTH') === 'true',
    googleAuth: getOptionalEnv('VITE_FEATURE_GOOGLE_AUTH') === 'true',
    orchestration: getOptionalEnv('VITE_FEATURE_ORCHESTRATION') === 'true',
    sandbox: getOptionalEnv('VITE_FEATURE_SANDBOX') === 'true',
    analytics: getOptionalEnv('VITE_ENABLE_ANALYTICS') === 'true',
    debugMode: getOptionalEnv('VITE_DEBUG_MODE') === 'true',
  },

  turnstile: {
    chat: getOptionalEnv('VITE_TURNSTILE_SITE_KEY_CHAT'),
    login: getOptionalEnv('VITE_TURNSTILE_SITE_KEY_LOGIN'),
    search: getOptionalEnv('VITE_TURNSTILE_SITE_KEY_SEARCH'),
  },

  sentryDsn: getOptionalEnv('VITE_SENTRY_DSN'),
  posthogApiKey: getOptionalEnv('VITE_POSTHOG_API_KEY'),
  posthogHost: getOptionalEnv('VITE_POSTHOG_HOST'),

  mode: (import.meta.env.MODE as EnvConfig['mode']) || 'development',
  isDevelopment: import.meta.env.MODE === 'development',
  isProduction: import.meta.env.MODE === 'production',
};

// Validate on import
validateEnvConfig(env);

// Log configuration in development
if (env.isDevelopment) {
  devLog('📝 Environment Configuration:', {
    ...env,
    apiBaseUrl: env.apiBaseUrl,
    mode: env.mode,
  });
}
