import { FastApiRuntimeClient } from './FastApiRuntimeClient';
import { DemoRuntimeClient } from './DemoRuntimeClient';
import { MockRuntimeClient } from './MockRuntimeClient';
import type { RuntimeClient } from '../types/api';

// Environment-based runtime selection
const RUNTIME: string = (import.meta.env.VITE_GOBLIN_RUNTIME as string) || 'fastapi';
const MOCK_API: boolean = import.meta.env.VITE_MOCK_API === 'true';

// Create runtime client instances
export const runtimeClientFast = new FastApiRuntimeClient();
export const runtimeClientMock = new MockRuntimeClient();
export const runtimeClientDemo = new DemoRuntimeClient();

// Dynamic selection of runtime client (keep runtimeClient name for compatibility)
// Priority: MOCK_API > RUNTIME environment variable > default to fastapi
export const runtimeClient: RuntimeClient = MOCK_API
  ? runtimeClientMock
  : RUNTIME === 'demo'
    ? runtimeClientDemo
    : runtimeClientFast;

// Export chosen runtime client (legacy compatibility)
export const runtime = runtimeClient;

// Export individual clients for direct access when needed
export { FastApiRuntimeClient, DemoRuntimeClient, MockRuntimeClient };

// Export types
export type { RuntimeClient } from '../types/api';
