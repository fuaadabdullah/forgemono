import { useState } from 'react';
import { apiClient } from '../api/client';

interface OrchestrationStep {
  id: string;
  goblin: string;
  task: string;
  dependencies: string[];
  batch: number;
}

interface OrchestrationPlan {
  steps: OrchestrationStep[];
  total_batches: number;
  max_parallel: number;
  estimated_cost: number;
}

const Orchestration = () => {
  const [input, setInput] = useState('');
  const [defaultGoblin, setDefaultGoblin] = useState('docs-writer');
  const [plan, setPlan] = useState<OrchestrationPlan | null>(null);
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

      setPlan(result);
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

      setExecutionId(result.execution_id);
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
        <h1 className="text-3xl font-bold text-white mb-2">Orchestration Planner</h1>
        <p className="text-gray-400">Create and execute multi-step task orchestrations</p>
      </div>

      {/* Input Form */}
      <div className="bg-gray-800 rounded-lg p-6">
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Orchestration Instructions
            </label>
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Describe the orchestration workflow (e.g., 'First analyze the code, then write documentation, finally create tests')"
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-blue-500 h-32 resize-none"
              disabled={loading}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Default Goblin
            </label>
            <select
              value={defaultGoblin}
              onChange={(e) => setDefaultGoblin(e.target.value)}
              className="px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              disabled={loading}
            >
              <option value="docs-writer">Documentation Writer</option>
              <option value="code-writer">Code Writer</option>
              <option value="search-goblin">Search Specialist</option>
              <option value="analyze-goblin">Data Analyst</option>
            </select>
          </div>

          <div className="flex space-x-4">
            <button
              onClick={parseOrchestration}
              disabled={loading || !input.trim()}
              className="px-6 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white font-semibold rounded-lg transition-colors"
            >
              {loading ? 'Parsing...' : 'Parse Orchestration'}
            </button>

            <button
              onClick={clearAll}
              className="px-6 py-2 bg-gray-600 hover:bg-gray-700 text-white font-semibold rounded-lg transition-colors"
            >
              Clear All
            </button>
          </div>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-red-900 border border-red-700 rounded-lg p-4">
          <h3 className="text-red-400 font-semibold">Error</h3>
          <p className="text-red-300">{error}</p>
        </div>
      )}

      {/* Orchestration Plan */}
      {plan && (
        <div className="bg-gray-800 rounded-lg p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-semibold text-white">Orchestration Plan</h2>
            <button
              onClick={executePlan}
              disabled={executing}
              className="px-6 py-2 bg-green-600 hover:bg-green-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white font-semibold rounded-lg transition-colors"
            >
              {executing ? 'Executing...' : 'Execute Plan'}
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div className="bg-gray-700 rounded-lg p-4">
              <div className="text-2xl font-bold text-blue-400">{plan.total_batches}</div>
              <div className="text-sm text-gray-400">Total Batches</div>
            </div>
            <div className="bg-gray-700 rounded-lg p-4">
              <div className="text-2xl font-bold text-purple-400">{plan.max_parallel}</div>
              <div className="text-sm text-gray-400">Max Parallel</div>
            </div>
            <div className="bg-gray-700 rounded-lg p-4">
              <div className="text-2xl font-bold text-green-400">${plan.estimated_cost.toFixed(4)}</div>
              <div className="text-sm text-gray-400">Estimated Cost</div>
            </div>
          </div>

          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-white">Execution Steps</h3>
            {plan.steps.map((step, index) => (
              <div key={step.id} className="bg-gray-700 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center space-x-3">
                    <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center text-white font-semibold">
                      {index + 1}
                    </div>
                    <div>
                      <h4 className="text-white font-semibold">{step.goblin}</h4>
                      <p className="text-gray-400 text-sm">Batch {step.batch}</p>
                    </div>
                  </div>
                  <div className="text-sm text-gray-400">
                    {step.dependencies.length > 0 && `Depends on: ${step.dependencies.join(', ')}`}
                  </div>
                </div>
                <p className="text-gray-300 ml-11">{step.task}</p>
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
