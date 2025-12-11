import React from 'react'
import ReactDOM from 'react-dom/client'
import { QueryClientProvider } from '@tanstack/react-query'
import App from './App.tsx'
import { ErrorBoundaryFallback } from './components/ErrorBoundary'
import './index.css'
import { queryClient } from './lib/queryClient'
import { logErrorToService } from './utils/monitoring'
import { env } from './config/env'
import { devLog } from './utils/dev-log'
import { inject } from '@vercel/analytics'
import posthog from 'posthog-js'

devLog('🚀 main.tsx loading...');
devLog('API Base URL:', env.fastApiUrl);

// Initialize Vercel Analytics if enabled
if (env.features.analytics) {
  inject();
}

// Initialize PostHog for user analytics (optional)
if (env.posthogApiKey && env.isProduction) {
  posthog.init(env.posthogApiKey, {
    api_host: env.posthogHost || 'https://app.posthog.com',
    capture_pageview: true,
    capture_pageleave: true,
    persistence: 'localStorage',
    // Respect user privacy
    mask_all_text: true,
    mask_all_element_attributes: true,
    // Disable autocapture for sensitive forms
    autocapture: false,
  });
}

const rootElement = document.getElementById('root');

if (!rootElement) {
  throw new Error('Root element not found');
}

const root = ReactDOM.createRoot(rootElement);

// ✅ Safe error handling - no innerHTML
try {
  root.render(
    <React.StrictMode>
      <QueryClientProvider client={queryClient}>
        <App />
      </QueryClientProvider>
    </React.StrictMode>,
  );
  devLog('✅ React app rendered successfully');
} catch (error) {
  // Log to monitoring service (not console in production)
  if (env.isProduction) {
    // Send to Sentry
    logErrorToService(error as Error);
  } else {
    console.error('App initialization failed:', error);
  }

  // ✅ Render safe error UI
  root.render(<ErrorBoundaryFallback error={error as Error} />);
}
