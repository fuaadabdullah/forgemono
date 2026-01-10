import type {
  RuntimeClient,
  GoblinStatus,
  MemoryEntry,
  GoblinStats,
  CostSummary,
  OrchestrationPlan,
  StreamChunk,
  TaskResponse,
  User,
  DemoStepData,
} from '../types/api';

// Demo runtime client for interview demonstrations - provides deterministic, pre-recorded responses
export class DemoRuntimeClient implements RuntimeClient {
  // Pre-recorded responses for common orchestration templates
  private readonly demoResponses = {
    'docs-writer: document this code THEN code-writer: write a unit test': {
      'docs-writer': {
        response: `# add(a, b) Function Documentation

## Overview
A simple arithmetic function that adds two numbers together.

## Parameters
- \`a\` (number): The first number to add
- \`b\` (number): The second number to add

## Returns
- \`number\`: The sum of a and b

## Example Usage
\`\`\`javascript
const result = add(5, 3); // Returns 8
\`\`\`

## Notes
This function performs basic addition without any error checking or type validation.`,
        cost: 0.012,
        tokens: 156,
      },
      'code-writer': {
        response: `# Unit Test for add() Function

\`\`\`javascript
describe('add() function', () => {
  test('adds two positive numbers correctly', () => {
    expect(add(2, 3)).toBe(5);
    expect(add(10, 15)).toBe(25);
  });

  test('adds positive and negative numbers correctly', () => {
    expect(add(5, -3)).toBe(2);
    expect(add(-2, -3)).toBe(-5);
  });

  test('adds with zero correctly', () => {
    expect(add(0, 5)).toBe(5);
    expect(add(5, 0)).toBe(5);
    expect(add(0, 0)).toBe(0);
  });

  test('handles decimal numbers', () => {
    expect(add(1.5, 2.5)).toBe(4);
    expect(add(0.1, 0.2)).toBeCloseTo(0.3);
  });
});
\`\`\``,
        cost: 0.018,
        tokens: 203,
      },
    },
    'code-writer: analyze this code for issues THEN code-writer: suggest optimizations': {
      'code-writer': {
        response: `# Code Analysis: add() Function

## Issues Found
1. **No input validation**: Function doesn't check if inputs are numbers
2. **No error handling**: Will return NaN for invalid inputs like strings
3. **Limited type safety**: No TypeScript types or JSDoc annotations
4. **No edge case handling**: Doesn't handle very large numbers or special values

## Potential Runtime Issues
- \`add("5", "3")\` returns "53" (string concatenation)
- \`add(null, 5)\` returns 5 (type coercion)
- \`add(undefined, 5)\` returns NaN
- \`add(Infinity, -Infinity)\` returns NaN

## Recommendations
1. Add input type checking
2. Add JSDoc documentation
3. Consider using TypeScript for better type safety
4. Add error handling for edge cases`,
        cost: 0.015,
        tokens: 178,
      },
      'code-writer-2': {
        response: `# Optimization Suggestions for add() Function

## Performance Optimizations
1. **Use strict equality**: No changes needed for simple addition
2. **Avoid unnecessary operations**: Current implementation is already optimal

## Code Quality Improvements
\`\`\`javascript
/**
 * Adds two numbers together
 * @param {number} a - First number
 * @param {number} b - Second number
 * @returns {number} Sum of a and b
 * @throws {TypeError} If inputs are not numbers
 */
function add(a, b) {
  if (typeof a !== 'number' || typeof b !== 'number') {
    throw new TypeError('Both arguments must be numbers');
  }
  if (!isFinite(a) || !isFinite(b)) {
    throw new RangeError('Arguments must be finite numbers');
  }
  return a + b;
}
\`\`\`

## Benefits of Changes
- **Type Safety**: Prevents string concatenation and type coercion
- **Error Handling**: Clear error messages for invalid inputs
- **Documentation**: JSDoc provides better IDE support
- **Edge Case Handling**: Prevents NaN results from Infinity/-Infinity

## Alternative: TypeScript Version
\`\`\`typescript
function add(a: number, b: number): number {
  return a + b;
}
\`\`\``,
        cost: 0.022,
        tokens: 245,
      },
    },
  };

  async getGoblins(): Promise<GoblinStatus[]> {
    return [
      {
        id: 'docs-writer',
        name: 'docs-writer',
        title: 'Documentation Writer',
        status: 'available',
      },
      { id: 'code-writer', name: 'code-writer', title: 'Code Writer', status: 'available' },
    ];
  }

  async getProviders(): Promise<string[]> {
    return ['demo'];
  }

  async getProviderModels(_provider: string): Promise<string[]> {
    return ['demo-model'];
  }

  async executeTask(
    _goblin: string,
    _task: string,
    _streaming = false,
    _code?: string,
    _provider?: string,
    _model?: string
  ): Promise<string> {
    // Simulate async delay for realism
    await new Promise((resolve) => setTimeout(resolve, 200));
    return `demo_task_${_goblin}_${Date.now()}`;
  }

  async getHistory(_goblin: string, _limit = 10): Promise<MemoryEntry[]> {
    return [];
  }

  async getStats(_goblin: string): Promise<GoblinStats> {
    return { total_tasks: 42, success_rate: 0.98 };
  }

  async getCostSummary(): Promise<CostSummary> {
    return {
      total_cost: 0.15,
      cost_by_provider: { demo: 0.15 },
      cost_by_model: { 'demo-model': 0.15 },
    };
  }

  async parseOrchestration(text: string, defaultGoblin?: string): Promise<OrchestrationPlan> {
    // Parse the orchestration text to create steps
    const stepTexts = text.split('THEN').map((s) => s.trim());
    const steps = stepTexts.map((stepText, index) => {
      const [goblin, ...taskParts] = stepText.split(':');
      return {
        id: `step${index + 1}`,
        goblin: goblin?.trim() || defaultGoblin || 'docs-writer',
        task: taskParts.join(':').trim(),
        dependencies: index > 0 ? [`step${index}`] : [],
        batch: 0,
      };
    });
    return {
      steps,
      total_batches: 1,
      max_parallel: 1,
    };
  }

  async executeTaskStreaming(
    goblin: string,
    task: string,
    onChunk: (chunk: StreamChunk) => void,
    onComplete?: (response: TaskResponse) => void,
    _code?: string,
    _provider?: string,
    _model?: string
  ): Promise<void> {
    // Find the appropriate demo response based on the full orchestration
    const fullOrchestration = this.findOrchestrationFromTask(goblin, task);
    const demoData = fullOrchestration
      ? this.demoResponses[fullOrchestration as keyof typeof this.demoResponses]
      : null;

    let response: string;
    let cost: number;
    let tokens: number;

    if (demoData && demoData[goblin as keyof typeof demoData]) {
      const stepData = demoData[goblin as keyof typeof demoData] as DemoStepData;
      response = stepData.response;
      cost = stepData.cost;
      tokens = stepData.tokens;
    } else {
      // Fallback response for unrecognized tasks
      response = `Demo response: ${goblin} completed task "${task}" successfully. This is a pre-recorded demonstration response.`;
      cost = 0.01;
      tokens = 25;
    }

    // Simulate streaming by sending chunks
    const words = response.split(' ');
    let totalTokens = 0;
    let totalCost = 0;

    for (let i = 0; i < words.length; i++) {
      // Simulate realistic typing delay
      await new Promise((resolve) => setTimeout(resolve, 30 + Math.random() * 20));

      const chunk = words[i] + (i < words.length - 1 ? ' ' : '');
      const chunkTokens = Math.ceil(chunk.length / 4); // Rough token estimation
      const chunkCost = (chunkTokens / tokens) * cost;

      totalTokens += chunkTokens;
      totalCost += chunkCost;

      onChunk({
        chunk,
        token_count: chunkTokens,
        cost_delta: chunkCost,
        taskId: `demo_${Date.now()}`,
        provider: 'demo',
        model: 'demo-model',
      });
    }

    // Send completion
    if (onComplete) {
      onComplete({
        result: response,
        cost: totalCost,
        tokens: totalTokens,
        model: 'demo-model',
        provider: 'demo',
        duration_ms: words.length * 50,
      });
    }
  }

  private findOrchestrationFromTask(goblin: string, task: string): string | null {
    // Try to match the current task to a known orchestration
    for (const [_orchestration, _responses] of Object.entries(this.demoResponses)) {
      if (
        _orchestration.includes(`${goblin}: ${task}`) ||
        _orchestration.includes(`${goblin}:${task}`)
      ) {
        return _orchestration;
      }
    }
    return null;
  }

  async onTaskStream(_callback: (payload: StreamChunk) => void) {
    /* no-op */
  }

  async setProviderApiKey(_provider: string, _key: string): Promise<void> {
    return;
  }

  async storeApiKey(_provider: string, _key: string): Promise<void> {
    return;
  }

  async getApiKey(_provider: string): Promise<string | null> {
    return 'demo-key';
  }

  async clearApiKey(_provider: string): Promise<void> {
    return;
  }

  // Authentication methods - demo implementation
  async login(email: string, _password: string): Promise<{ token: string; user: User }> {
    // Demo login - accepts any email with @demo.com
    if (!email.includes('@demo.com')) {
      throw new Error('Demo login requires @demo.com email');
    }
    return {
      token: 'demo-token-' + Date.now(),
      user: {
        id: 'demo-user',
        email: email,
      },
    };
  }

  async register(
    email: string,
    _password: string,
    _name?: string
  ): Promise<{ token: string; user: User }> {
    // Demo registration - accepts any email
    return {
      token: 'demo-token-' + Date.now(),
      user: {
        id: 'demo-user-' + Date.now(),
        email: email,
      },
    };
  }

  async logout(): Promise<void> {
    // Demo logout - no-op
    return;
  }

  async validateToken(token: string): Promise<{ valid: boolean; user?: User }> {
    // Demo token validation - accepts any token starting with 'demo-token'
    if (token.startsWith('demo-token-')) {
      return {
        valid: true,
        user: {
          id: 'demo-user',
          email: 'demo@example.com',
        },
      };
    }
    return { valid: false };
  }
}
