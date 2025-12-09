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
export async function typedFetch<T>(
  url: string,
  options?: RequestInit
): Promise<T> {
  const response = await fetch(url, options);

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  return response.json() as Promise<T>;
}

/**
 * Safe fetch with error handling and optional type guard validation
 */
export async function safeFetch<T>(
  url: string,
  options?: RequestInit,
  typeGuard?: (data: unknown) => data is T
): Promise<T | null> {
  try {
    const response = await fetch(url, options);
    const data = await response.json();

    if (typeGuard && !typeGuard(data)) {
      console.error('Invalid response type for:', url);
      return null;
    }

    return data as T;
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
  async chatCompletion(messages: Array<{role: string, content: string}>, model?: string): Promise<ChatCompletionResponse | null> {
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
 */
export async function handleApiResponse<T>(
  response: Response
): Promise<ApiResponse<T>> {
  const data = await response.json();

  if (!response.ok) {
    return {
      success: false,
      error: data.error || `HTTP ${response.status}`,
      code: data.code,
      details: data.details,
    };
  }

  return {
    success: true,
    data: data as T,
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
