import type {
  RuntimeClient,
  GoblinStatus,
  MemoryEntry,
  GoblinStats,
  CostSummary,
  OrchestrationPlan,
  StreamChunk,
  TaskResponse,
  User
} from '../types/api';

// Mock runtime client for testing - returns minimal responses
export class MockRuntimeClient implements RuntimeClient {
  async getGoblins(): Promise<GoblinStatus[]> {
    return [
      {
        id: 'mock-goblin',
        name: 'mock-goblin',
        title: 'Mock Goblin',
        status: 'available',
      },
    ];
  }

  async getProviders(): Promise<string[]> {
    return ['mock'];
  }

  async getProviderModels(_provider: string): Promise<string[]> {
    return ['mock-model'];
  }

  async executeTask(
    _goblin: string,
    _task: string,
    _streaming = false,
    _code?: string,
    _provider?: string,
    _model?: string
  ): Promise<string> {
    return 'mock_response';
  }

  async executeTaskStreaming(
    _goblin: string,
    _task: string,
    onChunk: (chunk: StreamChunk) => void,
    onComplete?: (response: TaskResponse) => void,
    _code?: string,
    _provider?: string,
    _model?: string
  ): Promise<void> {
    // Send a single mock chunk
    onChunk({
      chunk: 'mock response',
      token_count: 2,
      cost_delta: 0.001,
      taskId: 'mock-task',
      provider: 'mock',
      model: 'mock-model',
    });

    // Complete immediately
    if (onComplete) {
      onComplete({
        result: 'mock response',
        cost: 0.001,
        tokens: 2,
        model: 'mock-model',
        provider: 'mock',
        duration_ms: 10,
      });
    }
  }

  async getHistory(_goblin: string, _limit = 10): Promise<MemoryEntry[]> {
    return [];
  }

  async getStats(_goblin: string): Promise<GoblinStats> {
    return { total_tasks: 0, success_rate: 1.0 };
  }

  async getCostSummary(): Promise<CostSummary> {
    return {
      total_cost: 0.0,
      cost_by_provider: { mock: 0.0 },
      cost_by_model: { 'mock-model': 0.0 },
    };
  }

  async parseOrchestration(text: string, defaultGoblin?: string): Promise<OrchestrationPlan> {
    // Simple mock parsing - just return a basic plan
    return {
      steps: [
        {
          id: 'step1',
          goblin: defaultGoblin || 'mock-goblin',
          task: text,
          dependencies: [],
          batch: 0,
        },
      ],
      total_batches: 1,
      max_parallel: 1,
    };
  }

  async onTaskStream(_callback: (payload: StreamChunk) => void) {
    // No-op for mock
  }

  async setProviderApiKey(_provider: string, _key: string): Promise<void> {
    // No-op for mock
  }

  async storeApiKey(_provider: string, _key: string): Promise<void> {
    // No-op for mock
  }

  async getApiKey(_provider: string): Promise<string | null> {
    return 'mock-key';
  }

  async clearApiKey(_provider: string): Promise<void> {
    // No-op for mock
  }

  // Authentication methods - mock implementation
  async login(email: string, _password: string): Promise<{ token: string; user: User }> {
    return {
      token: 'mock-token',
      user: {
        id: 'mock-user',
        email: email,
      },
    };
  }

  async register(
    email: string,
    _password: string,
    _name?: string
  ): Promise<{ token: string; user: User }> {
    return {
      token: 'mock-token',
      user: {
        id: 'mock-user',
        email: email,
      },
    };
  }

  async logout(): Promise<void> {
    // No-op for mock
  }

  async validateToken(_token: string): Promise<{ valid: boolean; user?: User }> {
    return {
      valid: true,
      user: {
        id: 'mock-user',
        email: 'mock@example.com',
      },
    };
  }
}
