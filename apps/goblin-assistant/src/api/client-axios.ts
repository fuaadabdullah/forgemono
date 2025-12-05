import axios, { AxiosInstance, AxiosRequestConfig, AxiosError } from 'axios';
import { useAuthStore } from '../store/authStore';

// Check if running in Vercel environment
const IS_VERCEL = typeof window !== 'undefined' && window.location.hostname.includes('vercel.app');

const API_BASE_URL = IS_VERCEL ? '' : (import.meta.env.VITE_FASTAPI_URL || 'http://localhost:8001');

/**
 * Typed API client using axios with interceptors for auth and error handling
 */
class ApiClient {
  private client: AxiosInstance;

  constructor(baseUrl: string = API_BASE_URL) {
    this.client = axios.create({
      baseURL: baseUrl,
      headers: {
        'Content-Type': 'application/json',
      },
      timeout: 30000, // 30 second timeout
    });

    // Request interceptor: Add auth token
    this.client.interceptors.request.use(
      (config) => {
        const token = useAuthStore.getState().token;
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor: Handle auth errors
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        if (error.response?.status === 401) {
          // Clear auth on 401 Unauthorized
          useAuthStore.getState().clearAuth();
        }
        return Promise.reject(this.handleError(error));
      }
    );
  }

  private handleError(error: AxiosError): Error {
    if (error.response) {
      // Server responded with error status
      const message = (error.response.data as any)?.detail || error.message;
      return new Error(message);
    } else if (error.request) {
      // Request made but no response
      return new Error('Network error: No response from server');
    } else {
      // Something else went wrong
      return new Error(error.message);
    }
  }

  // Generic request method
  private async request<T>(config: AxiosRequestConfig): Promise<T> {
    const response = await this.client.request<T>(config);
    return response.data;
  }

  // ============ Health Endpoints ============
  async getHealth() {
    return this.request({ method: 'GET', url: '/health' });
  }

  async getStreamingHealth() {
    return this.request({ method: 'GET', url: '/api/health/stream' });
  }

  async getAllHealth() {
    return this.request({ method: 'GET', url: '/health/all' });
  }

  // ============ Dashboard Endpoints (Optimized) ============
  async getDashboardStatus(): Promise<{
    backend_api: { status: string; latency_ms?: number; error?: string; updated: string; details?: any };
    vector_db: { status: string; latency_ms?: number; error?: string; updated: string; details?: any };
    mcp_servers: { status: string; latency_ms?: number; error?: string; updated: string; details?: any };
    rag_indexer: { status: string; latency_ms?: number; error?: string; updated: string; details?: any };
    sandbox_runner: { status: string; latency_ms?: number; error?: string; updated: string; details?: any };
    timestamp: string;
  }> {
    return this.request({ method: 'GET', url: '/api/dashboard/status' });
  }

  async getDashboardCosts(): Promise<{
    total_cost: number;
    cost_today: number;
    cost_this_month: number;
    by_provider: Record<string, number>;
    timestamp: string;
  }> {
    return this.request({ method: 'GET', url: '/api/dashboard/costs' });
  }

  async getDashboardMetrics(service: string): Promise<{
    service: string;
    latency_history?: { timestamps: string[]; latencies: number[] };
    avg_latency_ms?: number;
    data_points?: number;
    message?: string;
    timestamp: string;
  }> {
    return this.request({ method: 'GET', url: `/api/dashboard/metrics/${service}` });
  }

  // Enhanced health endpoints for comprehensive monitoring (LEGACY - use dashboard endpoints instead)
  async getChromaStatus(): Promise<{ status: string; collections: number; documents: number; last_check: string }> {
    return this.request({ method: 'GET', url: '/health/chroma/status' });
  }

  async getMCPStatus(): Promise<{ status: string; servers: string[]; active_connections: number; last_check: string }> {
    return this.request({ method: 'GET', url: '/health/mcp/status' });
  }

  async getRaptorStatus(): Promise<{ status: string; running: boolean; config_file: string; last_check: string }> {
    return this.request({ method: 'GET', url: '/health/raptor/status' });
  }

  async getSandboxStatus(): Promise<{ status: string; active_jobs: number; queue_size: number; last_check: string }> {
    return this.request({ method: 'GET', url: '/health/sandbox/status' });
  }

  async getCostTracking(): Promise<{ total_cost: number; cost_today: number; cost_this_month: number; by_provider: any }> {
    return this.request({ method: 'GET', url: '/health/cost-tracking' });
  }

  async getLatencyHistory(service: string, hours: number = 24): Promise<{ timestamps: string[]; latencies: number[] }> {
    return this.request({
      method: 'GET',
      url: `/health/latency-history/${service}`,
      params: { hours },
    });
  }

  async getServiceErrors(service: string, limit: number = 10): Promise<any[]> {
    return this.request({
      method: 'GET',
      url: `/health/service-errors/${service}`,
      params: { limit },
    });
  }

  async retestService(service: string): Promise<{ success: boolean; latency: number | null; message: string }> {
    return this.request({
      method: 'POST',
      url: `/health/retest/${service}`,
    });
  }

  // ============ Authentication Endpoints ============
  async register(email: string, password: string): Promise<{ access_token: string; token_type: string }> {
    return this.request({
      method: 'POST',
      url: '/auth/register',
      data: { email, password },
      // Temporarily disabled turnstile header for backend compatibility
      // headers: turnstileToken ? { 'X-Turnstile-Token': turnstileToken } : {},
    });
  }

  async login(email: string, password: string): Promise<{ access_token: string; token_type: string }> {
    return this.request({
      method: 'POST',
      url: '/auth/login',
      data: { email, password },
      // Temporarily disabled turnstile header for backend compatibility
      // headers: turnstileToken ? { 'X-Turnstile-Token': turnstileToken } : {},
    });
  }

  async loginWithGoogle(credential: string): Promise<{ access_token: string; token_type: string }> {
    return this.request({
      method: 'POST',
      url: '/auth/google',
      data: { credential },
    });
  }

  async getGoogleAuthUrl(): Promise<{ url: string }> {
    return this.request({ method: 'GET', url: '/auth/google/url' });
  }

  async googleCallback(code: string, state: string): Promise<{ access_token: string; token_type: string }> {
    return this.request({
      method: 'POST',
      url: '/auth/google/callback',
      data: { code, state },
    });
  }

  async passkeyChallenge(email: string) {
    return this.request({
      method: 'POST',
      url: '/auth/passkey/challenge',
      data: { email },
    });
  }

  async passkeyRegister(email: string, credential: any) {
    return this.request({
      method: 'POST',
      url: '/auth/passkey/register',
      data: { email, credential },
    });
  }

  async passkeyAuth(email: string, assertion: any): Promise<{ access_token: string; token_type: string }> {
    return this.request({
      method: 'POST',
      url: '/auth/passkey/auth',
      data: { email, assertion },
    });
  }

  async validateToken(token: string) {
    return this.request({
      method: 'POST',
      url: '/auth/validate',
      data: { token },
    });
  }

  async logout() {
    try {
      await this.request({ method: 'POST', url: '/auth/logout' });
    } finally {
      useAuthStore.getState().clearAuth();
    }
  }

  // ============ Chat Endpoints ============
  async chatCompletion(messages: any[], model?: string, stream?: boolean, turnstileToken?: string) {
    return this.request({
      method: 'POST',
      url: '/chat/completions',
      data: { messages, model, stream },
      headers: turnstileToken ? { 'X-Turnstile-Token': turnstileToken } : {},
    });
  }

  async getAvailableModels(): Promise<any[]> {
    return this.request({ method: 'GET', url: '/chat/models' });
  }

  async getRoutingInfo() {
    return this.request({ method: 'GET', url: '/chat/routing-info' });
  }

  // ============ Routing Endpoints ============
  async getProviders(capability?: string): Promise<any[]> {
    const url = capability ? `/routing/providers/${capability}` : '/routing/providers';
    return this.request({ method: 'GET', url });
  }

  async routeRequest(request: any) {
    return this.request({
      method: 'POST',
      url: '/routing/route',
      data: request,
    });
  }

  async getRoutingHealth() {
    return this.request({ method: 'GET', url: '/routing/health' });
  }

  // ============ Settings Endpoints ============
  async getAllSettings(): Promise<{ providers: any; global_settings: any }> {
    return this.request({ method: 'GET', url: '/settings/' });
  }

  async getProviderSettings(): Promise<any[]> {
    // Legacy method - returns providers from getAllSettings
    const settings = await this.getAllSettings();
    return Object.values(settings.providers || {});
  }

  async updateProvider(providerNameOrId: string | number, data: any) {
    // Accept both provider name (string) and ID (number) for backward compatibility
    const providerName = typeof providerNameOrId === 'number' ? String(providerNameOrId) : providerNameOrId;
    return this.request({
      method: 'PUT',
      url: `/settings/providers/${providerName}`,
      data,
    });
  }

  async updateModel(modelName: string, data: any) {
    return this.request({
      method: 'PUT',
      url: `/settings/models/${modelName}`,
      data,
    });
  }

  async testConnection(providerName: string, apiKey?: string): Promise<{ success: boolean; message: string; latency?: number }> {
    return this.request({
      method: 'POST',
      url: '/settings/test-connection',
      params: { provider_name: providerName },
      data: { api_key: apiKey },
    });
  }

  async testProviderConnection(providerId: number): Promise<{ success: boolean; message: string; latency?: number }> {
    // Legacy method - use testConnection with provider name lookup
    // For now, return a placeholder that works with existing UI
    return this.testConnection(String(providerId));
  }

  async testProviderWithPrompt(providerId: number, prompt: string): Promise<{
    success: boolean;
    message: string;
    latency: number;
    response?: string;
    model_used?: string;
  }> {
    return this.request({
      method: 'POST',
      url: `/settings/providers/${providerId}/test-prompt`,
      data: { prompt },
    });
  }

  async reorderProviders(providerIds: number[]): Promise<{ success: boolean }> {
    return this.request({
      method: 'POST',
      url: '/settings/providers/reorder',
      data: { provider_ids: providerIds },
    });
  }

  async setProviderPriority(providerId: number, priority: number, role?: 'primary' | 'fallback'): Promise<{ success: boolean }> {
    return this.request({
      method: 'POST',
      url: `/settings/providers/${providerId}/priority`,
      data: { priority, role },
    });
  }

  async updateGlobalSetting(_key: string, _value: string) {
    // Backend doesn't have this endpoint yet - return success for now
    console.warn('updateGlobalSetting not implemented in backend');
    return { success: true, message: 'Global settings update not implemented' };
  }

  async getModelConfigs(): Promise<any[]> {
    // Legacy method - returns empty for now
    console.warn('getModelConfigs not implemented in backend');
    return [];
  }

  async getGlobalSettings(): Promise<any> {
    // Legacy method - returns global_settings from getAllSettings
    const settings = await this.getAllSettings();
    return settings.global_settings || {};
  }

  async createCollection(_name: string, _description?: string) {
    // Legacy method - not implemented in current backend
    console.warn('createCollection not implemented in backend');
    throw new Error('createCollection endpoint not available');
  }

  async searchDocuments(collectionIdOrName: number | string, query: string, _limit?: number): Promise<any[]> {
    // Legacy method - maps to searchQuery, accepts both ID and name for backward compatibility
    const collectionName = typeof collectionIdOrName === 'number' ? String(collectionIdOrName) : collectionIdOrName;
    const result = await this.searchQuery(query, collectionName);
    return result.results || [];
  }

  async indexDocument(collectionIdOrName: number | string, content: string, metadata?: any) {
    // Legacy method - maps to addDocument, accepts both ID and name for backward compatibility
    const collectionName = typeof collectionIdOrName === 'number' ? String(collectionIdOrName) : collectionIdOrName;
    return this.addDocument(collectionName, { content, metadata });
  }

  // ============ Search Endpoints ============
  async searchQuery(query: string, collectionName?: string): Promise<any> {
    return this.request({
      method: 'POST',
      url: '/search/query',
      data: { query, collection_name: collectionName },
    });
  }

  async getCollections(): Promise<any[]> {
    return this.request({ method: 'GET', url: '/search/collections' });
  }

  async getCollectionDocuments(collectionName: string): Promise<any[]> {
    return this.request({
      method: 'GET',
      url: `/search/collections/${collectionName}/documents`,
    });
  }

  async addDocument(collectionName: string, document: any) {
    return this.request({
      method: 'POST',
      url: `/search/collections/${collectionName}/add`,
      data: document,
    });
  }

  // ============ API Keys Endpoints ============
  async getApiKey(provider: string): Promise<any> {
    return this.request({
      method: 'GET',
      url: `/api-keys/${provider}`,
    });
  }

  async setApiKey(provider: string, apiKey: string, keyType: string = 'api_key') {
    return this.request({
      method: 'POST',
      url: `/api-keys/${provider}`,
      data: { api_key: apiKey, key_type: keyType },
    });
  }

  async deleteApiKey(provider: string) {
    return this.request({
      method: 'DELETE',
      url: `/api-keys/${provider}`,
    });
  }

  // ============ RAPTOR Endpoints ============
  async startRaptor() {
    return this.request({ method: 'POST', url: '/raptor/start' });
  }

  async stopRaptor() {
    return this.request({ method: 'POST', url: '/raptor/stop' });
  }

  async getRaptorLogs(limit?: number): Promise<any[]> {
    return this.request({
      method: 'POST',
      url: '/raptor/logs',
      data: { limit },
    });
  }

  // ============ Sandbox Endpoints ============
  async getSandboxJobs(): Promise<any[]> {
    return this.request({ method: 'GET', url: '/sandbox/jobs' });
  }

  async getJobLogs(jobId: string) {
    return this.request({ method: 'GET', url: `/sandbox/jobs/${jobId}/logs` });
  }

  async getJobArtifacts(jobId: string): Promise<any[]> {
    return this.request({ method: 'GET', url: `/sandbox/jobs/${jobId}/artifacts` });
  }

  // ============ Debugger Endpoints ============
  async getSuggestions(code: string, error: string) {
    return this.request({
      method: 'POST',
      url: '/debugger/suggest',
      data: { code, error },
    });
  }

  // ============ Goblin Management ============
  async getGoblins(): Promise<any[]> {
    return this.request({ method: 'GET', url: '/api/goblins' });
  }

  async getGoblinHistory(goblinId: string, limit: number = 10): Promise<any[]> {
    return this.request({
      method: 'GET',
      url: `/api/history/${goblinId}`,
      params: { limit },
    });
  }

  async getGoblinStats(goblinId: string) {
    return this.request({ method: 'GET', url: `/api/stats/${goblinId}` });
  }

  // ============ Task Routing ============
  async routeTask(taskData: {
    task_type: string;
    payload: any;
    prefer_local?: boolean;
    prefer_cost?: boolean;
    max_retries?: number;
    stream?: boolean;
  }) {
    return this.request({
      method: 'POST',
      url: '/api/route_task',
      data: taskData,
    });
  }

  // ============ Streaming Task Execution ============
  async startStreamingTask(taskData: {
    goblin: string;
    task: string;
    code?: string;
    provider?: string;
    model?: string;
  }): Promise<{ stream_id: string; status: string }> {
    return this.request({
      method: 'POST',
      url: '/api/route_task_stream_start',
      data: taskData,
    });
  }

  async pollStreamingTask(streamId: string) {
    return this.request({
      method: 'GET',
      url: `/api/route_task_stream_poll/${streamId}`,
    });
  }

  async cancelStreamingTask(streamId: string) {
    return this.request({
      method: 'POST',
      url: `/api/route_task_stream_cancel/${streamId}`,
    });
  }

  // ============ Orchestration ============
  async createOrchestrationPlan(request: { text: string; default_goblin?: string }) {
    return this.request({
      method: 'POST',
      url: '/execute/',
      data: request,
    });
  }

  async executeOrchestration(planId: string) {
    return this.request({
      method: 'POST',
      url: '/execute/orchestrate/execute',
      params: { plan_id: planId },
    });
  }

  async parseOrchestration(request: { text: string }) {
    return this.request({
      method: 'POST',
      url: '/execute/orchestrate/parse',
      data: request,
    });
  }

  async getOrchestrationPlan(planId: string) {
    return this.request({
      method: 'GET',
      url: `/execute/orchestrate/plans/${planId}`,
    });
  }

  async getExecutionStatus(taskId: string) {
    return this.request({
      method: 'GET',
      url: `/execute/status/${taskId}`,
    });
  }

  // ============ Streaming Endpoint (EventSource - not axios) ============
  streamTaskExecution(taskId: string, goblin: string = 'default', task: string = 'default task'): EventSource {
    const url = `${API_BASE_URL}/stream?task_id=${encodeURIComponent(taskId)}&goblin=${encodeURIComponent(goblin)}&task=${encodeURIComponent(task)}`;
    return new EventSource(url);
  }
}

export const apiClient = new ApiClient();
