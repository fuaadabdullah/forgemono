// API client for GoblinOS Assistant backend
const API_BASE_URL = import.meta.env.VITE_FASTAPI_URL || 'http://localhost:8001';

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  private async request(endpoint: string, options: RequestInit = {}): Promise<any> {
    const url = `${this.baseUrl}${endpoint}`;
    const config: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    };

    try {
      const response = await fetch(url, config);
      if (!response.ok) {
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

  // Authentication
  async validateToken(token: string): Promise<any> {
    return this.request('/auth/validate', {
      method: 'POST',
      body: JSON.stringify({ token }),
    });
  }

  async logout(): Promise<any> {
    return this.request('/auth/logout', {
      method: 'POST',
    });
  }

  // Streaming endpoint for real-time updates
  async streamTaskExecution(taskId: string, goblin: string = 'default', task: string = 'default task'): Promise<EventSource> {
    const url = `${this.baseUrl}/stream?task_id=${encodeURIComponent(taskId)}&goblin=${encodeURIComponent(goblin)}&task=${encodeURIComponent(task)}`;
    return new EventSource(url);
  }
}

export const apiClient = new ApiClient();
