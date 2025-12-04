// API client for GoblinOS Assistant backend
// Use relative URLs in production (Vercel proxy) or full URLs in development
const IS_VERCEL = import.meta.env.VITE_VERCEL === '1' || import.meta.env.VERCEL === '1';
const API_BASE_URL = IS_VERCEL ? '' : (import.meta.env.VITE_FASTAPI_URL || 'http://localhost:8001');

class ApiClient {
  private baseUrl: string;
  private authToken: string | null = null;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
    // Load auth token from localStorage if available
    this.authToken = localStorage.getItem('auth_token');
  }

  setAuthToken(token: string | null) {
    this.authToken = token;
    if (token) {
      localStorage.setItem('auth_token', token);
    } else {
      localStorage.removeItem('auth_token');
    }
  }

  private async request(endpoint: string, options: RequestInit = {}): Promise<any> {
    const url = `${this.baseUrl}${endpoint}`;
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options.headers as Record<string, string>),
    };

    // Add auth token if available
    if (this.authToken) {
      headers['Authorization'] = `Bearer ${this.authToken}`;
    }

    const config: RequestInit = {
      headers,
      ...options,
    };

    try {
      const response = await fetch(url, config);
      if (!response.ok) {
        if (response.status === 401) {
          // Clear invalid token
          this.setAuthToken(null);
        }
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error(`API request failed: ${endpoint}`, error);
      throw error;
    }
  }

  // Health endpoints
  async getHealth(): Promise<any> {
    return this.request('/health');
  }

  async getStreamingHealth(): Promise<any> {
    return this.request('/api/health/stream');
  }

  async getAllHealth(): Promise<any> {
    return this.request('/health/all');
  }

  // Authentication endpoints
  async register(email: string, password: string, turnstileToken?: string): Promise<{ access_token: string; token_type: string }> {
    const headers: Record<string, string> = {};
    if (turnstileToken) {
      headers['X-Turnstile-Token'] = turnstileToken;
    }

    return this.request('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
      headers,
    });
  }

  async login(email: string, password: string, turnstileToken?: string): Promise<{ access_token: string; token_type: string }> {
    const headers: Record<string, string> = {};
    if (turnstileToken) {
      headers['X-Turnstile-Token'] = turnstileToken;
    }

    return this.request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
      headers,
    });
  }

  async loginWithGoogle(credential: string): Promise<{ access_token: string; token_type: string }> {
    return this.request('/auth/google', {
      method: 'POST',
      body: JSON.stringify({ credential }),
    });
  }

  async getGoogleAuthUrl(): Promise<{ url: string }> {
    return this.request('/auth/google/url');
  }

  async googleCallback(code: string, state: string): Promise<{ access_token: string; token_type: string }> {
    return this.request('/auth/google/callback', {
      method: 'POST',
      body: JSON.stringify({ code, state }),
    });
  }

  async passkeyChallenge(email: string): Promise<any> {
    return this.request('/auth/passkey/challenge', {
      method: 'POST',
      body: JSON.stringify({ email }),
    });
  }

  async passkeyRegister(email: string, credential: any): Promise<any> {
    return this.request('/auth/passkey/register', {
      method: 'POST',
      body: JSON.stringify({ email, credential }),
    });
  }

  async passkeyAuth(email: string, assertion: any): Promise<{ access_token: string; token_type: string }> {
    return this.request('/auth/passkey/auth', {
      method: 'POST',
      body: JSON.stringify({ email, assertion }),
    });
  }

  async validateToken(token: string): Promise<any> {
    return this.request('/auth/validate', {
      method: 'POST',
      body: JSON.stringify({ token }),
    });
  }

  async logout(): Promise<any> {
    this.setAuthToken(null);
    return this.request('/auth/logout', {
      method: 'POST',
    });
  }

  // Chat endpoints
  async chatCompletion(messages: any[], model?: string, stream?: boolean, turnstileToken?: string): Promise<any> {
    const headers: Record<string, string> = {};
    if (turnstileToken) {
      headers['X-Turnstile-Token'] = turnstileToken;
    }

    return this.request('/chat/completions', {
      method: 'POST',
      body: JSON.stringify({ messages, model, stream }),
      headers,
    });
  }

  async getAvailableModels(): Promise<any[]> {
    return this.request('/chat/models');
  }

  async getRoutingInfo(): Promise<any> {
    return this.request('/chat/routing-info');
  }

  // Routing endpoints
  async getProviders(capability?: string): Promise<any[]> {
    const endpoint = capability ? `/routing/providers/${capability}` : '/routing/providers';
    return this.request(endpoint);
  }

  async routeRequest(request: any): Promise<any> {
    return this.request('/routing/route', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async getRoutingHealth(): Promise<any> {
    return this.request('/routing/health');
  }

  // Settings endpoints
  async getProviderSettings(): Promise<any[]> {
    return this.request('/settings/providers');
  }

  async createProvider(provider: any): Promise<any> {
    return this.request('/settings/providers', {
      method: 'POST',
      body: JSON.stringify(provider),
    });
  }

  async updateProvider(providerId: number, provider: any): Promise<any> {
    return this.request(`/settings/providers/${providerId}`, {
      method: 'PUT',
      body: JSON.stringify(provider),
    });
  }

  async deleteProvider(providerId: number): Promise<any> {
    return this.request(`/settings/providers/${providerId}`, {
      method: 'DELETE',
    });
  }

  async getCredentials(): Promise<any[]> {
    return this.request('/settings/credentials');
  }

  async createCredential(credential: any): Promise<any> {
    return this.request('/settings/credentials', {
      method: 'POST',
      body: JSON.stringify(credential),
    });
  }

  async updateCredential(credentialId: number, credential: any): Promise<any> {
    return this.request(`/settings/credentials/${credentialId}`, {
      method: 'PUT',
      body: JSON.stringify(credential),
    });
  }

  async deleteCredential(credentialId: number): Promise<any> {
    return this.request(`/settings/credentials/${credentialId}`, {
      method: 'DELETE',
    });
  }

  async getModelConfigs(): Promise<any[]> {
    return this.request('/settings/models');
  }

  async createModelConfig(config: any): Promise<any> {
    return this.request('/settings/models', {
      method: 'POST',
      body: JSON.stringify(config),
    });
  }

  async updateModelConfig(configId: number, config: any): Promise<any> {
    return this.request(`/settings/models/${configId}`, {
      method: 'PUT',
      body: JSON.stringify(config),
    });
  }

  async deleteModelConfig(configId: number): Promise<any> {
    return this.request(`/settings/models/${configId}`, {
      method: 'DELETE',
    });
  }

  async getGlobalSettings(): Promise<any[]> {
    return this.request('/settings/global');
  }

  async updateGlobalSetting(key: string, value: string): Promise<any> {
    return this.request('/settings/global', {
      method: 'PUT',
      body: JSON.stringify({ key, value }),
    });
  }

  // Search endpoints
  async createCollection(name: string, description?: string): Promise<any> {
    return this.request('/search/collections', {
      method: 'POST',
      body: JSON.stringify({ name, description }),
    });
  }

  async getCollections(): Promise<any[]> {
    return this.request('/search/collections');
  }

  async indexDocument(collectionId: number, content: string, metadata?: any): Promise<any> {
    return this.request('/search/documents', {
      method: 'POST',
      body: JSON.stringify({ collection_id: collectionId, content, metadata }),
    });
  }

  async searchDocuments(collectionId: number, query: string, limit?: number): Promise<any[]> {
    return this.request('/search/search', {
      method: 'POST',
      body: JSON.stringify({ collection_id: collectionId, query, limit }),
    });
  }

  // API Keys endpoints
  async getApiKeys(): Promise<any[]> {
    return this.request('/api-keys');
  }

  async createApiKey(name: string, provider: string): Promise<any> {
    return this.request('/api-keys', {
      method: 'POST',
      body: JSON.stringify({ name, provider }),
    });
  }

  async deleteApiKey(keyId: number): Promise<any> {
    return this.request(`/api-keys/${keyId}`, {
      method: 'DELETE',
    });
  }

  // RAPTOR endpoints
  async startRaptor(): Promise<any> {
    return this.request('/raptor/start', {
      method: 'POST',
    });
  }

  async stopRaptor(): Promise<any> {
    return this.request('/raptor/stop', {
      method: 'POST',
    });
  }

  async getRaptorStatus(): Promise<any> {
    return this.request('/raptor/status');
  }

  async getRaptorLogs(limit?: number): Promise<any[]> {
    return this.request('/raptor/logs', {
      method: 'POST',
      body: JSON.stringify({ limit }),
    });
  }

  // Sandbox endpoints
  async getSandboxJobs(): Promise<any[]> {
    return this.request('/sandbox/jobs');
  }

  async getJobLogs(jobId: string): Promise<any> {
    return this.request(`/sandbox/jobs/${jobId}/logs`);
  }

  async getJobArtifacts(jobId: string): Promise<any[]> {
    return this.request(`/sandbox/jobs/${jobId}/artifacts`);
  }

  // Debugger endpoints
  async getSuggestions(code: string, error: string): Promise<any> {
    return this.request('/debugger/suggest', {
      method: 'POST',
      body: JSON.stringify({ code, error }),
    });
  }

  // Goblin management
  async getGoblins(): Promise<any[]> {
    return this.request('/api/goblins');
  }

  async getGoblinHistory(goblinId: string, limit: number = 10): Promise<any[]> {
    return this.request(`/api/history/${goblinId}?limit=${limit}`);
  }

  async getGoblinStats(goblinId: string): Promise<any> {
    return this.request(`/api/stats/${goblinId}`);
  }

  // Task routing
  async routeTask(taskData: {
    task_type: string;
    payload: any;
    prefer_local?: boolean;
    prefer_cost?: boolean;
    max_retries?: number;
    stream?: boolean;
  }): Promise<any> {
    return this.request('/api/route_task', {
      method: 'POST',
      body: JSON.stringify(taskData),
    });
  }

  // Streaming task execution
  async startStreamingTask(taskData: {
    goblin: string;
    task: string;
    code?: string;
    provider?: string;
    model?: string;
  }): Promise<{ stream_id: string; status: string }> {
    return this.request('/api/route_task_stream_start', {
      method: 'POST',
      body: JSON.stringify(taskData),
    });
  }

  async pollStreamingTask(streamId: string): Promise<any> {
    return this.request(`/api/route_task_stream_poll/${streamId}`);
  }

  async cancelStreamingTask(streamId: string): Promise<any> {
    return this.request(`/api/route_task_stream_cancel/${streamId}`, {
      method: 'POST',
    });
  }

  // Orchestration
  async parseOrchestration(request: {
    text: string;
    default_goblin?: string;
  }): Promise<any> {
    return this.request('/api/orchestrate/parse', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async executeOrchestration(planId: string): Promise<any> {
    return this.request(`/api/orchestrate/execute?plan_id=${planId}`, {
      method: 'POST',
    });
  }

  async getOrchestrationPlan(planId: string): Promise<any> {
    return this.request(`/api/orchestrate/plans/${planId}`);
  }

  // Streaming endpoint for real-time updates
  async streamTaskExecution(taskId: string, goblin: string = 'default', task: string = 'default task'): Promise<EventSource> {
    const url = `${this.baseUrl}/stream?task_id=${encodeURIComponent(taskId)}&goblin=${encodeURIComponent(goblin)}&task=${encodeURIComponent(task)}`;
    return new EventSource(url);
  }
}

export const apiClient = new ApiClient();
