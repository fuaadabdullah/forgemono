import { useState } from 'react';
import { apiClient } from '../api/client-axios';
import { Button, Alert } from './ui';

interface OrchestrationStep {
  id: string;
  goblin: string;
  task: string;
  dependencies: string[];
  batch: number;
}

interface LocalOrchestrationPlan {
  steps: OrchestrationStep[];
  total_batches: number;
  max_parallel: number;
  estimated_cost: number;
}

const Orchestration = () => {
  const [input, setInput] = useState('');
  const [defaultGoblin, setDefaultGoblin] = useState('docs-writer');
  const [plan, setPlan] = useState<LocalOrchestrationPlan | null>(null);
  const [executionId, setExecutionId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [executing, setExecuting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const parseOrchestration = async () => {
    if (!input.trim()) {
      setError('Please enter orchestration instructions');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      setPlan(null);
      setExecutionId(null);

      const result = await apiClient.parseOrchestration({
        text: input.trim(),
        default_goblin: defaultGoblin,
      });

      setPlan(result as any);
    } catch (err) {
      setError('Failed to parse orchestration');
      console.error('Parse orchestration error:', err);
    } finally {
      setLoading(false);
    }
  };

  const executePlan = async () => {
    if (!plan) return;

    try {
      setExecuting(true);
      setError(null);

      // For demo purposes, we'll use a mock plan ID
      const planId = `plan_${Date.now()}`;
      const result = await apiClient.executeOrchestration(planId);

      setExecutionId((result as any).execution_id);
    } catch (err) {
      setError('Failed to execute orchestration');
      console.error('Execute orchestration error:', err);
    } finally {
      setExecuting(false);
    }
  };

  const clearAll = () => {
    setInput('');
    setPlan(null);
    setExecutionId(null);
    setError(null);
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="text-center">
        <h1 className="text-3xl font-bold text-text mb-2">Orchestration Planner</h1>
        <p className="text-muted">Create and execute multi-step task orchestrations</p>
      </div>

      {/* Live region for orchestration updates */}
      <div className="sr-only" role="status" aria-live="polite" aria-atomic="true">
        {plan && `Orchestration plan created with ${plan.steps.length} step${plan.steps.length !== 1 ? 's' : ''} in ${plan.total_batches} batch${plan.total_batches !== 1 ? 'es' : ''}`}
        {executionId && `Orchestration started with ID ${executionId}`}
      </div>

      {/* Input Form */}
      <div className="bg-surface rounded-lg p-6 border border-border">
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-muted mb-2">
              Orchestration Instructions
            </label>
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Describe the orchestration workflow (e.g., 'First analyze the code, then write documentation, finally create tests')"
              className="w-full px-3 py-2 bg-surface-hover border border-border rounded-md text-text placeholder-muted focus:outline-none focus:ring-2 focus:ring-primary h-32 resize-none"
              disabled={loading}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-muted mb-2">
              Default Goblin
            </label>
            <select
              value={defaultGoblin}
              onChange={(e) => setDefaultGoblin(e.target.value)}
              className="px-3 py-2 bg-surface-hover border border-border rounded-md text-text focus:outline-none focus:ring-2 focus:ring-primary"
              disabled={loading}
            >
              <option value="docs-writer">Documentation Writer</option>
              <option value="code-writer">Code Writer</option>
              <option value="search-goblin">Search Specialist</option>
              <option value="analyze-goblin">Data Analyst</option>
            </select>
          </div>

          <div className="flex space-x-4">
            <Button
              onClick={parseOrchestration}
              disabled={loading || !input.trim()}
              loading={loading}
              variant="primary"
            >
              Parse Orchestration
            </Button>

            <Button
              onClick={clearAll}
              variant="secondary"
            >
              Clear All
            </Button>
          </div>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <Alert
          variant="danger"
          title="Error"
          message={error}
          dismissible
          onDismiss={() => setError(null)}
        />
      )}

      {/* Orchestration Plan */}
      {plan && (
        <div className="bg-surface rounded-lg p-6 border border-border">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-semibold text-text">Orchestration Plan</h2>
            <Button
              onClick={executePlan}
              disabled={executing}
              loading={executing}
              variant="success"
            >
              Execute Plan
            </Button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div className="bg-surface-hover rounded-lg p-4 border border-border">
              <div className="text-2xl font-bold text-primary">{plan.total_batches}</div>
              <div className="text-sm text-muted">Total Batches</div>
            </div>
            <div className="bg-surface-hover rounded-lg p-4 border border-border">
              <div className="text-2xl font-bold text-accent">{plan.max_parallel}</div>
              <div className="text-sm text-muted">Max Parallel</div>
            </div>
            <div className="bg-surface-hover rounded-lg p-4 border border-border">
              <div className="text-2xl font-bold text-success">${plan.estimated_cost.toFixed(4)}</div>
              <div className="text-sm text-muted">Estimated Cost</div>
            </div>
          </div>

          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-text">Execution Steps</h3>
            {plan.steps.map((step, index) => (
              <div key={step.id} className="bg-surface-hover rounded-lg p-4 border border-border">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center space-x-3">
                    <div className="w-8 h-8 bg-primary rounded-full flex items-center justify-center text-text-inverse font-semibold shadow-glow-primary">
                      {index + 1}
                    </div>
                    <div>
                      <h4 className="text-text font-semibold">{step.goblin}</h4>
                      <p className="text-muted text-sm">Batch {step.batch}</p>
                    </div>
                  </div>
                  <div className="text-sm text-muted">
                    {step.dependencies.length > 0 && `Depends on: ${step.dependencies.join(', ')}`}
                  </div>
                </div>
                <p className="text-text ml-11">{step.task}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Execution Result */}
      {executionId && (
        <div className="bg-green-900 border border-green-700 rounded-lg p-4">
          <h3 className="text-green-400 font-semibold">Orchestration Started</h3>
          <p className="text-green-300">Execution ID: {executionId}</p>
          <p className="text-green-300 text-sm mt-2">
            The orchestration plan is now being executed. Check the execution status using the plan ID.
          </p>
        </div>
      )}
    </div>
  );
};

export default Orchestration;
