import { api } from '../lib/api/http-client';

// ============================================================================
// Raptor AI Service Control Functions
// ============================================================================

/**
 * Starts the Raptor AI inference service
 *
 * Initializes and starts the Raptor backend service that handles AI model inference,
 * caching, and performance optimization. This service must be running for AI features
 * to work properly.
 *
 * @returns Promise resolving to service status after startup attempt
 * @throws {Error} When service fails to start or API is unreachable
 *
 * @example
 * ```typescript
 * try {
 *   const status = await raptorStart();
 *   if (status.running) {
 *     console.log('Raptor service started successfully');
 *   }
 * } catch (error) {
 *   console.error('Failed to start Raptor:', error);
 * }
 * ```
 */
export async function raptorStart(): Promise<{ running: boolean }> {
  const response = await api.post<{ running: boolean }>('/raptor/start');
  return response.data;
}

/**
 * Stops the Raptor AI inference service
 *
 * Gracefully shuts down the Raptor backend service, stopping all active
 * model inference operations and cleaning up resources.
 *
 * @returns Promise resolving to service status after shutdown attempt
 * @throws {Error} When service fails to stop or API is unreachable
 */
export async function raptorStop(): Promise<{ running: boolean }> {
  const response = await api.post<{ running: boolean }>('/raptor/stop');
  return response.data;
}

/**
 * Gets the current status of the Raptor AI inference service
 *
 * Checks if the Raptor service is running and returns configuration information
 * if available. This is useful for monitoring service health and debugging.
 *
 * @returns Promise resolving to service status and optional config file path
 * @throws {Error} When API is unreachable
 */
export async function raptorStatus(): Promise<{ running: boolean; config_file?: string }> {
  const response = await api.get<{ running: boolean; config_file?: string }>('/raptor/status');
  return response.data;
}

/**
 * Retrieves recent logs from the Raptor AI inference service
 *
 * Gets the tail of the service logs for debugging and monitoring purposes.
 * Useful for troubleshooting service issues or monitoring performance.
 *
 * @param maxChars Maximum number of characters to return (default: 4000)
 * @returns Promise resolving to log tail content
 * @throws {Error} When service is not running or API is unreachable
 */
export async function raptorLogs(maxChars = 4000): Promise<{ log_tail: string }> {
  const response = await api.post<{ log_tail: string }>('/raptor/logs', { max_chars: maxChars });
  return response.data;
}

/**
 * Runs a demo operation on the Raptor AI inference service
 *
 * Executes a simple demonstration of the Raptor service capabilities.
 * Useful for testing service connectivity and basic functionality.
 *
 * @param value Input value for the demo operation
 * @returns Promise resolving to demo result
 * @throws {Error} When service is not running or API is unreachable
 */
export async function raptorDemo(value: string): Promise<{ result: string }> {
  const response = await api.get<{ result: string }>(`/raptor/demo/${encodeURIComponent(value)}`);
  return response.data;
}
