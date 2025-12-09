// src/types/api.ts
// Comprehensive API response types for the application

// ============================================================================
// Auth API Types
// ============================================================================

export interface PasskeyChallenge {
  publicKey: {
    challenge: string;
    rp: {
      name: string;
      id: string;
    };
    user: {
      id: string;
      name: string;
      displayName: string;
    };
    pubKeyCredParams: Array<{
      type: string;
      alg: number;
    }>;
    timeout?: number;
    attestation?: string;
    authenticatorSelection?: {
      authenticatorAttachment?: string;
      requireResidentKey?: boolean;
      userVerification?: string;
    };
  };
}

export interface PasskeyVerificationChallenge {
  publicKey: {
    challenge: string;
    rpId?: string;
    allowCredentials?: Array<{
      type: string;
      id: string;
    }>;
    timeout?: number;
    userVerification?: string;
  };
}

// ============================================================================
// Consolidated Auth API Types
// ============================================================================

export interface User {
  id: string;
  email: string;
  role?: string;
  roles?: string[];
  token_version?: number;
  created_at?: string;
  updated_at?: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface RefreshTokenRequest {
  refresh_token: string;
}

export interface RefreshTokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface UserSession {
  id: string;
  user_id: string;
  refresh_token_id: string;
  device_info?: string;
  ip_address?: string;
  user_agent?: string;
  created_at: string;
  last_active: string;
  expires_at: string;
  revoked: boolean;
  revoked_at?: string;
  revoked_reason?: string;
}

export interface SessionsResponse {
  sessions: UserSession[];
  total: number;
}

export interface RevokeSessionRequest {
  session_id: string;
}

export interface EmergencyLogoutResponse {
  message: string;
  revoked_sessions: number;
}

export interface AuthError {
  detail: string;
  code?: string;
  type?: 'authentication' | 'authorization' | 'validation' | 'server';
}

// ============================================================================
// Health Check Types
// ============================================================================

export interface ServiceHealth {
  status: 'healthy' | 'degraded' | 'unhealthy';
  latency?: number;
  message?: string;
}

export interface HealthStatus {
  overall: 'healthy' | 'degraded' | 'unhealthy';
  timestamp: string;
  services: {
    database?: ServiceHealth;
    cache?: ServiceHealth;
    api?: ServiceHealth;
    [key: string]: ServiceHealth | undefined;
  };
  uptime?: number;
}

// ============================================================================
// Orchestration Types
// ============================================================================

export interface OrchestrationPlan {
  id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  tasks: Array<{
    id: string;
    name: string;
    description: string;
    status: 'pending' | 'running' | 'completed' | 'failed';
    dependencies?: string[];
    estimated_duration?: number;
  }>;
  created_at: string;
  updated_at?: string;
  metadata?: Record<string, unknown>;
}

export interface CreateOrchestrationRequest {
  text: string;
  default_goblin?: string;
  context?: Record<string, unknown>;
}

export interface CreateOrchestrationResponse {
  plan: OrchestrationPlan;
  execution_id?: string;
}

// ============================================================================
// Task Execution Types
// ============================================================================

export interface TaskChunk {
  type: 'status' | 'output' | 'error' | 'complete';
  task_id?: string;
  content: string;
  timestamp: string;
  metadata?: Record<string, unknown>;
}

export interface TaskExecutionResponse {
  chunks: TaskChunk[];
  done: boolean;
  execution_id: string;
  total_tasks?: number;
  completed_tasks?: number;
}

export interface ExecutionResult {
  execution_id: string;
  status: 'completed' | 'failed' | 'running';
  results: Array<{
    task_id: string;
    output: string;
    status: 'success' | 'failed';
    error?: string;
  }>;
  started_at: string;
  completed_at?: string;
}

// ============================================================================
// Chat/Completion Types
// ============================================================================

export interface ChatMessage {
  role: 'system' | 'user' | 'assistant';
  content: string;
}

export interface ChatChoice {
  index: number;
  message: ChatMessage;
  finish_reason: string | null;
}

export interface UsageInfo {
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
}

export interface ChatCompletionResponse {
  id: string;
  object: string;
  created: number;
  model: string;
  choices: ChatChoice[];
  content?: string; // Direct content field for simpler responses
  usage?: UsageInfo;
}

// ============================================================================
// Generic API Response Wrappers
// ============================================================================

export interface ApiSuccessResponse<T = unknown> {
  success: true;
  data: T;
  message?: string;
}

export interface ApiErrorResponse {
  success: false;
  error: string;
  code?: string;
  details?: Record<string, unknown>;
}

export type ApiResponse<T = unknown> = ApiSuccessResponse<T> | ApiErrorResponse;

// ============================================================================
// Type Guards
// ============================================================================

export function isApiError(response: unknown): response is ApiErrorResponse {
  return (
    typeof response === 'object' &&
    response !== null &&
    'success' in response &&
    response.success === false
  );
}

export function isApiSuccess<T>(response: unknown): response is ApiSuccessResponse<T> {
  return (
    typeof response === 'object' &&
    response !== null &&
    'success' in response &&
    response.success === true
  );
}

export function isHealthStatus(data: unknown): data is HealthStatus {
  return (
    typeof data === 'object' &&
    data !== null &&
    'overall' in data &&
    'services' in data
  );
}

export function isOrchestrationPlan(data: unknown): data is OrchestrationPlan {
  return (
    typeof data === 'object' &&
    data !== null &&
    'id' in data &&
    'status' in data &&
    'tasks' in data &&
    Array.isArray((data as OrchestrationPlan).tasks)
  );
}

export function isTaskExecutionResponse(data: unknown): data is TaskExecutionResponse {
  return (
    typeof data === 'object' &&
    data !== null &&
    'chunks' in data &&
    'done' in data &&
    Array.isArray((data as TaskExecutionResponse).chunks)
  );
}

export function isChatCompletionResponse(data: unknown): data is ChatCompletionResponse {
  return (
    typeof data === 'object' &&
    data !== null &&
    ('choices' in data || 'content' in data)
  );
}
