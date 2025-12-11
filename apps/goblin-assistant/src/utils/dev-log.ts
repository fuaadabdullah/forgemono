/**
 * Development-only logging utility
 * Console logs are automatically removed in production builds
 */

import { env } from '../config/env';

/**
 * Log only in development environment
 */
export function devLog(...args: any[]): void {
  if (env.isDevelopment) {
    console.log(...args);
  }
}

/**
 * Log warnings in all environments (but with dev prefix in production)
 */
export function devWarn(...args: any[]): void {
  if (env.isDevelopment) {
    console.warn(...args);
  } else {
    // In production, still log critical warnings but mark as dev-only
    console.warn('[DEV-ONLY]', ...args);
  }
}

/**
 * Log errors in all environments
 */
export function devError(...args: any[]): void {
  console.error(...args);
}
