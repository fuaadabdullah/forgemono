// src/utils/api.ts
// Generic API utility functions for type-safe fetch operations

import {
  isApiError,
  isApiSuccess,
  isHealthStatus,
  isOrchestrationPlan,
  isTaskExecutionResponse,
  isChatCompletionResponse,
  type ApiResponse,
  type HealthStatus,
  type OrchestrationPlan,
  type TaskExecutionResponse,
  type ChatCompletionResponse,
} from '../types/api';

/**
 * Typed fetch wrapper that ensures type safety for API responses
 */
/**
 * Type-safe wrapper around fetch that automatically parses JSON responses
 *
 * This utility provides compile-time type safety for API responses while handling
 * the common pattern of fetching and parsing JSON. It throws on HTTP errors.
 *
 * @template T - The expected response type
 * @param url - The URL to fetch from
 * @param options - Standard fetch options (method, headers, etc.)
 * @returns Promise resolving to the typed JSON response
 * @throws {Error} When HTTP response is not ok (status >= 400)
 *
 * @example
 * ```typescript
 * interface User { id: number; name: string; }
 * const user = await typedFetch<User>('/api/users/123');
 * console.log(user.name); // TypeScript knows this is a string
 * ```
 */
export async function typedFetch<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(url, options);

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  return response.json() as Promise<T>;
}

/**
 * Safe fetch with error handling and optional type guard validation
 *
 * This function provides resilient API calls that gracefully handle network errors
 * and optionally validate response types at runtime. Unlike typedFetch, it returns
 * null on errors instead of throwing, making it suitable for non-critical operations.
 *
 * @template T - The expected response type
 * @param url - The URL to fetch from
 * @param options - Standard fetch options (method, headers, etc.)
 * @param typeGuard - Optional function to validate response shape at runtime
 * @returns Promise resolving to typed response or null if fetch/validation fails
 *
 * @example
 * ```typescript
 * // Basic usage - returns null on any error
 * const user = await safeFetch<User>('/api/users/123');
 *
 * // With type validation
 * const isValidUser = (data: unknown): data is User =>
 *   typeof data === 'object' && data !== null && 'id' in data;
 * const user = await safeFetch<User>('/api/users/123', {}, isValidUser);
 * ```
 */
export async function safeFetch<T>(
  url: string,
  options?: RequestInit,
  typeGuard?: (data: unknown) => data is T
): Promise<T | null> {
  try {
    const response = await fetch(url, options);
    const responseData = await response.json();

    if (typeGuard && !typeGuard(responseData)) {
      console.error('Invalid response type for:', url);
      return null;
    }

    return responseData as T;
  } catch (error) {
    console.error('Fetch error:', error);
    return null;
  }
}

/**
 * Specialized fetch functions for common API endpoints
 */
export const apiFetch = {
  /**
   * Fetch health status with type validation
   */
  async health(): Promise<HealthStatus | null> {
    return safeFetch<HealthStatus>('/api/health', undefined, isHealthStatus);
  },

  /**
   * Fetch orchestration plan with type validation
   */
  async orchestrationPlan(planId: string): Promise<OrchestrationPlan | null> {
    return safeFetch<OrchestrationPlan>(
      `/api/orchestration/plans/${planId}`,
      undefined,
      isOrchestrationPlan
    );
  },

  /**
   * Fetch task execution status with type validation
   */
  async taskExecution(executionId: string): Promise<TaskExecutionResponse | null> {
    return safeFetch<TaskExecutionResponse>(
      `/api/execution/${executionId}/stream`,
      undefined,
      isTaskExecutionResponse
    );
  },

  /**
   * Fetch chat completion with type validation
   */
  async chatCompletion(
    messages: Array<{ role: string; content: string }>,
    model?: string
  ): Promise<ChatCompletionResponse | null> {
    return safeFetch<ChatCompletionResponse>(
      '/api/chat/completions',
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ messages, model }),
      },
      isChatCompletionResponse
    );
  },
};

/**
 * Generic API response handler with error checking
 *
 * Standardizes API response handling by wrapping successful responses in a success
 * envelope and failed responses in an error envelope. This provides consistent
 * error handling patterns across the application.
 *
 * @template T - The expected success response type
 * @param response - The fetch Response object to process
 * @returns Promise resolving to standardized ApiResponse envelope
 *
 * @example
 * ```typescript
 * const response = await fetch('/api/users');
 * const result = await handleApiResponse<User[]>(response);
 *
 * if (result.success) {
 *   console.log('Users:', result.data);
 * } else {
 *   console.error('Error:', result.error);
 * }
 * ```
 */
export async function handleApiResponse<T>(response: Response): Promise<ApiResponse<T>> {
  const responseData = await response.json();

  if (!response.ok) {
    return {
      success: false,
      error: responseData.error || `HTTP ${response.status}`,
      code: responseData.code,
      details: responseData.details,
    };
  }

  return {
    success: true,
    data: responseData as T,
  };
}

/**
 * Validate API response using type guards
 */
export function validateApiResponse<T>(
  response: unknown,
  typeGuard: (data: unknown) => data is T
): response is ApiResponse<T> {
  if (isApiSuccess(response)) {
    return typeGuard(response.data);
  }

  return isApiError(response);
}
