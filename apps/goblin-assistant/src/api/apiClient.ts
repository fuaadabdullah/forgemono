import { api } from './http-client';
import type {
  LoginRequest,
  LoginResponse,
  RefreshTokenRequest,
  RefreshTokenResponse,
  SessionsResponse,
  RevokeSessionRequest,
  EmergencyLogoutResponse,
  PasskeyChallenge,
  PasskeyVerificationChallenge,
  CreateOrchestrationRequest,
  CreateOrchestrationResponse,
  HealthStatus,
  CostSummary,
  GoblinStatus,
  SettingsResponse,
} from '../types/api';

const createLocalId = (): string => {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID();
  }
  return `local-${Date.now()}-${Math.random().toString(16).slice(2, 10)}`;
};

export const apiClient = {
  // Health
  async getHealth(): Promise<unknown> {
    const response = await api.get('/health');
    return response.data;
  },
  async getAllHealth(): Promise<HealthStatus | unknown> {
    const response = await api.get('/health/all');
    return response.data;
  },
  async getStreamingHealth(): Promise<unknown> {
    const response = await api.get('/health/streaming');
    return response.data;
  },
  async getRoutingHealth(): Promise<unknown> {
    const response = await api.get('/health/routing');
    return response.data;
  },

  // Runtime data
  async getGoblins(): Promise<GoblinStatus[]> {
    const response = await api.get<GoblinStatus[]>('/goblins');
    return response.data || [];
  },
  async getProviders(): Promise<string[]> {
    const response = await api.get<string[]>('/routing/providers');
    return response.data || [];
  },
  async getProviderModels(provider: string): Promise<string[]> {
    const response = await api.get<string[]>(`/routing/providers/${provider}`);
    return response.data || [];
  },
  async getAvailableModels(): Promise<string[]> {
    const response = await api.get<string[]>('/routing/models');
    return response.data || [];
  },
  async getRoutingInfo(): Promise<unknown> {
    const response = await api.get('/routing/info');
    return response.data;
  },
  async getCostSummary(): Promise<CostSummary> {
    const response = await api.get<CostSummary>('/cost-summary');
    return response.data;
  },

  // Chat
  async createConversation(title?: string): Promise<{
    conversationId: string;
    title?: string;
    createdAt: string;
  }> {
    return {
      conversationId: createLocalId(),
      title,
      createdAt: new Date().toISOString(),
    };
  },
  async chatCompletion(messages: unknown[], model?: string, stream?: boolean): Promise<unknown> {
    const response = await api.post('/chat/completions', { messages, model, stream });
    return response.data;
  },

  // Simple chat using /api/generate endpoint (no auth required, automatic provider fallback)
  async generate(
    prompt: string,
    model?: string
  ): Promise<{
    content: string;
    usage?: { total_tokens?: number };
    model?: string;
    provider?: string;
  }> {
    const response = await api.post<{
      content: string;
      usage?: { total_tokens?: number };
      model?: string;
      provider?: string;
    }>(
      '/api/generate',
      { prompt, model: model || 'gemma:2b' },
      { timeout: 60000 }
    );
    return response.data;
  },

  // Search / RAG
  async getSearchCollections(): Promise<string[]> {
    const response = await api.get<{ collections: string[] }>('/search/collections');
    return response.data?.collections || [];
  },
  async searchQuery(
    collectionName: string,
    query: string,
    limit = 10
  ): Promise<{ results: unknown[]; total_results: number }> {
    const response = await api.post('/search/query', {
      query,
      collection_name: collectionName,
      n_results: limit,
    });
    return response.data as { results: unknown[]; total_results: number };
  },
  async getCollections(): Promise<unknown> {
    const response = await api.get('/collections');
    return response.data;
  },
  async createCollection(name: string, description?: string): Promise<unknown> {
    const response = await api.post('/collections', { name, description });
    return response.data;
  },
  async searchDocuments(collectionId: number, query: string, limit?: number): Promise<unknown> {
    const response = await api.post(`/collections/${collectionId}/search`, { query, limit });
    return response.data;
  },
  async indexDocument(collectionId: number, content: string, metadata?: unknown): Promise<unknown> {
    const response = await api.post(`/collections/${collectionId}/documents`, {
      content,
      metadata,
    });
    return response.data;
  },

  // Settings
  async getProviderSettings(): Promise<SettingsResponse | unknown> {
    const response = await api.get('/settings/providers');
    return response.data;
  },
  async getModelConfigs(): Promise<SettingsResponse | unknown> {
    const response = await api.get('/settings/models');
    return response.data;
  },
  async getGlobalSettings(): Promise<SettingsResponse | unknown> {
    const response = await api.get('/settings/global');
    return response.data;
  },
  async updateProvider(providerId: number, provider: unknown): Promise<unknown> {
    const response = await api.put(`/settings/providers/${providerId}`, provider);
    return response.data;
  },
  async updateGlobalSetting(key: string, value: string): Promise<unknown> {
    const response = await api.put(`/settings/global/${key}`, { value });
    return response.data;
  },

  // Providers
  async testProviderConnection(providerId: number): Promise<unknown> {
    const response = await api.post(`/providers/${providerId}/test`);
    return response.data;
  },
  async testProviderWithPrompt(providerId: number, prompt: string): Promise<unknown> {
    const response = await api.post(`/providers/${providerId}/test`, { prompt });
    return response.data;
  },
  async setProviderPriority(providerId: number, priority: number, role?: string): Promise<unknown> {
    const response = await api.post(`/providers/${providerId}/priority`, { priority, role });
    return response.data;
  },
  async reorderProviders(providerIds: number[]): Promise<unknown> {
    const response = await api.post('/providers/reorder', { providerIds });
    return response.data;
  },

  // Orchestration
  async parseOrchestration(
    payload: CreateOrchestrationRequest
  ): Promise<CreateOrchestrationResponse> {
    const response = await api.post<CreateOrchestrationResponse>('/orchestration/parse', payload);
    return response.data;
  },
  async executeOrchestration(planId: string): Promise<unknown> {
    const response = await api.post(`/orchestration/execute/${planId}`);
    return response.data;
  },

  // Raptor
  async getRaptorLogs(tail = 100): Promise<{ log_tail: string }> {
    const response = await api.get<{ log_tail: string }>(`/raptor/logs?tail=${tail}`);
    return response.data;
  },

  // Sandbox
  async getSandboxJobs(): Promise<unknown> {
    const response = await api.get('/sandbox/jobs');
    return response.data;
  },
  async getJobLogs(jobId: string): Promise<unknown> {
    const response = await api.get(`/sandbox/jobs/${jobId}/logs`);
    return response.data;
  },
  async runSandboxCode(payload: { code: string; language: string }): Promise<{ output: string }> {
    const response = await api.post('/sandbox/run', payload);
    return response.data as { output: string };
  },

  // Account
  async saveAccountProfile(payload: { name: string }): Promise<unknown> {
    const response = await api.post('/account/profile', payload);
    return response.data;
  },
  async saveAccountPreferences(payload: {
    summaries: boolean;
    notifications: boolean;
    familyMode: boolean;
  }): Promise<unknown> {
    const response = await api.post('/account/preferences', payload);
    return response.data;
  },

  // Support
  async sendSupportMessage(message: string): Promise<unknown> {
    const response = await api.post('/support/message', { message });
    return response.data;
  },

  // Auth
  async login(payload: LoginRequest | string, password?: string): Promise<LoginResponse> {
    const body = typeof payload === 'string' ? { email: payload, password } : payload;
    const response = await api.post<LoginResponse>('/auth/login', body);
    return response.data;
  },
  async register(email: string, password: string, turnstileToken?: string): Promise<LoginResponse> {
    const response = await api.post<LoginResponse>('/auth/register', {
      email,
      password,
      turnstile_token: turnstileToken,
    });
    return response.data;
  },
  async refreshToken(payload: RefreshTokenRequest): Promise<RefreshTokenResponse> {
    const response = await api.post<RefreshTokenResponse>('/auth/refresh', payload);
    return response.data;
  },
  async getSessions(): Promise<SessionsResponse> {
    const response = await api.get<SessionsResponse>('/auth/sessions');
    return response.data;
  },
  async revokeSession(payload: RevokeSessionRequest): Promise<unknown> {
    const response = await api.post('/auth/sessions/revoke', payload);
    return response.data;
  },
  async emergencyLogout(): Promise<EmergencyLogoutResponse> {
    const response = await api.post<EmergencyLogoutResponse>('/auth/sessions/revoke-all');
    return response.data;
  },
  async logout(): Promise<void> {
    await api.post('/auth/logout');
  },
  async getGoogleAuthUrl(): Promise<{ url: string }> {
    const response = await api.get<{ url: string }>('/auth/google/url');
    return response.data;
  },
  async passkeyChallenge(email: string): Promise<PasskeyChallenge | PasskeyVerificationChallenge> {
    const response = await api.post<PasskeyChallenge | PasskeyVerificationChallenge>(
      '/auth/passkey/challenge',
      { email }
    );
    return response.data;
  },
  async passkeyRegister(email: string, credential: unknown): Promise<unknown> {
    const response = await api.post('/auth/passkey/register', { email, credential });
    return response.data;
  },
  async passkeyAuth(email: string, assertion: unknown): Promise<LoginResponse> {
    const response = await api.post<LoginResponse>('/auth/passkey/auth', { email, assertion });
    return response.data;
  },
};

export type { LoginRequest, LoginResponse };
