import React, { useState, ReactNode } from 'react';
import { useProviderSettings, ProviderConfig } from '../hooks/api/useSettings';
import { useRoutingHealth } from '../hooks/api/useHealth';
import { apiClient } from '../api/client-axios';
import TwoColumnLayout from '../components/TwoColumnLayout';
import { Button, Alert } from '../components/ui';
import { ProviderCardSkeleton } from '../components/LoadingSkeleton';

interface TestResult {
  success: boolean;
  message: string;
  latency: number;
  response?: string;
  model_used?: string;
}

/**
 * Enhanced Provider Manager
 * Test, reorder, set priorities, and manage AI provider routing
 */
export default function EnhancedProvidersPage() {
  const { data: providers, isLoading, error, refetch } = useProviderSettings();
  const { data: routingHealth } = useRoutingHealth();

  const providerList = (providers as ProviderConfig[] | undefined) || [];
  const routingStatus: string = (routingHealth as any)?.status || 'Healthy';

  const [selectedProvider, setSelectedProvider] = useState<ProviderConfig | null>(null);
  const [testing, setTesting] = useState<string | null>(null);
  const [testResult, setTestResult] = useState<TestResult | null>(null);
  const [testPrompt, setTestPrompt] = useState('Write a hello world in Python');
  const [draggedProvider, setDraggedProvider] = useState<ProviderConfig | null>(null);
  const [reordering, setReordering] = useState(false);

  const handleQuickTest = async (provider: ProviderConfig) => {
    setTesting(provider.name);
    setTestResult(null);

    try {
      if (provider.id) {
        const result = await apiClient.testProviderConnection(provider.id);
        setTestResult({
          success: result.success,
          message: result.message,
          latency: result.latency || 0,
        });
      }
    } catch (error) {
      setTestResult({
        success: false,
        message: error instanceof Error ? error.message : 'Connection test failed',
        latency: 0,
      });
    } finally {
      setTesting(null);
    }
  };

  const handlePromptTest = async () => {
    if (!selectedProvider || !selectedProvider.id) return;

    setTesting(selectedProvider.name);
    setTestResult(null);

    try {
      const result = await apiClient.testProviderWithPrompt(
        selectedProvider.id,
        testPrompt
      );
      setTestResult(result);
    } catch (error) {
      setTestResult({
        success: false,
        message: error instanceof Error ? error.message : 'Test failed',
        latency: 0,
      });
    } finally {
      setTesting(null);
    }
  };

  const handleSetPriority = async (providerId: number, priority: number, role?: 'primary' | 'fallback') => {
    try {
      await apiClient.setProviderPriority(providerId, priority, role);
      await refetch();
    } catch (error) {
      console.error('Failed to set priority:', error);
    }
  };

  const handleReorder = async (newOrder: ProviderConfig[]) => {
    setReordering(true);
    try {
      const providerIds = newOrder.map(p => p.id).filter((id): id is number => id !== undefined);
      await apiClient.reorderProviders(providerIds);
      await refetch();
    } catch (error) {
      console.error('Failed to reorder providers:', error);
    } finally {
      setReordering(false);
    }
  };

  const handleDragStart = (provider: ProviderConfig) => {
    setDraggedProvider(provider);
  };

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
  };

  const handleDrop = (targetProvider: ProviderConfig) => {
    if (!draggedProvider || draggedProvider.id === targetProvider.id) return;

    const newOrder = [...providerList];
    const draggedIndex = newOrder.findIndex(p => p.id === draggedProvider.id);
    const targetIndex = newOrder.findIndex(p => p.id === targetProvider.id);

    newOrder.splice(draggedIndex, 1);
    newOrder.splice(targetIndex, 0, draggedProvider);

    handleReorder(newOrder);
    setDraggedProvider(null);
  };

  const sidebar: ReactNode = (
    <div className="space-y-4">
      <div>
        <h2 className="text-lg font-semibold text-text mb-3">Providers</h2>
        <p className="text-xs text-muted mb-4">
          Manage AI provider connections, priorities, and routing order
        </p>
      </div>

      {/* Quick Actions */}
      <div className="space-y-2">
        <Button
          variant="primary"
          size="sm"
          fullWidth
          icon="🔄"
          onClick={() => refetch()}
          disabled={isLoading}
          loading={isLoading}
          aria-label="Refresh provider status"
        >
          Refresh Status
        </Button>
        <button className="w-full px-3 py-2 text-sm font-medium text-text bg-surface-hover rounded-lg hover:bg-surface-active transition-colors">
          ➕ Add Provider
        </button>
      </div>

      {/* Routing Health */}
      {!!routingHealth && (
        <div className="bg-surface rounded-lg p-3 border border-border">
          <h3 className="text-sm font-medium text-text mb-2">Routing Engine</h3>
          <div className="text-xs text-muted">
            <div className="flex justify-between">
              <span>Status:</span>
              <span className="font-medium text-success">{routingStatus}</span>
            </div>
          </div>
        </div>
      )}

      {/* Provider List with Drag & Drop */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <h3 className="text-xs font-semibold text-text uppercase tracking-wide">
            Providers (Drag to Reorder)
          </h3>
          {reordering && (
            <span className="text-xs text-primary animate-pulse">Saving...</span>
          )}
        </div>

        {isLoading ? (
          <div className="space-y-2" role="status" aria-label="Loading providers">
            {[1, 2, 3].map((i) => (
              <ProviderCardSkeleton key={i} />
            ))}
            <span className="sr-only">Loading providers...</span>
          </div>
        ) : providerList.length > 0 ? (
          providerList.map((provider, index) => (
            <div
              key={provider.id || provider.name}
              draggable
              onDragStart={() => handleDragStart(provider)}
              onDragOver={handleDragOver}
              onDrop={() => handleDrop(provider)}
              onClick={() => setSelectedProvider(provider)}
              className={`cursor-move px-3 py-2 rounded-lg text-sm transition-all ${
                selectedProvider?.name === provider.name
                  ? 'bg-primary/20 text-primary border-2 border-primary'
                  : 'bg-surface border border-border hover:border-primary/50'
              } ${draggedProvider?.id === provider.id ? 'opacity-50' : ''}`}
            >
              <div className="flex items-center gap-2">
                <span className="text-muted text-xs font-mono">#{index + 1}</span>
                <span className="flex-1 font-medium">{provider.name}</span>
                <div className="flex items-center gap-1">
                  {provider.priority && provider.priority <= 1 && (
                    <span className="text-xs px-1.5 py-0.5 rounded bg-info/20 text-info">
                      PRIMARY
                    </span>
                  )}
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleQuickTest(provider);
                    }}
                    disabled={testing === provider.name}
                    className="text-xs hover:text-success"
                  >
                    {testing === provider.name ? '🔄' : '🧪'}
                  </button>
                  <span className={`text-xs ${provider.enabled ? 'text-success' : 'text-muted'}`}>
                    {provider.enabled ? '✓' : '○'}
                  </span>
                </div>
              </div>
            </div>
          ))
        ) : (
          <div className="text-xs text-muted">No providers configured</div>
        )}
      </div>
    </div>
  );

  const mainContent = (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-text mb-2">
          Provider Manager & Tester
        </h1>
        <p className="text-muted">
          Configure, test with prompts, and set priorities for intelligent routing
        </p>
      </div>

      {/* Live region for provider updates */}
      <div className="sr-only" role="status" aria-live="polite" aria-atomic="true">
        {!isLoading && providerList.length > 0 && `Providers loaded. ${providerList.length} provider${providerList.length !== 1 ? 's' : ''} available`}
        {testResult && `Test ${testResult.success ? 'passed' : 'failed'}. ${testResult.message}`}
      </div>

      {error && (
        <Alert
          variant="danger"
          title="Failed to Load Providers"
          message={
            <>
              <p className="mb-3">{(error as Error).message}</p>
              <Button
                variant="danger"
                size="sm"
                icon="🔄"
                onClick={() => refetch()}
                aria-label="Retry loading providers"
              >
                Retry
              </Button>
            </>
          }
          dismissible
        />
      )}

      {selectedProvider ? (
        <div className="space-y-6">
          {/* Provider Header */}
          <div className="bg-surface rounded-xl shadow-sm border border-border p-6">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className="text-2xl font-semibold text-text">
                  {selectedProvider.name}
                </h2>
                <p className="text-sm text-muted">Provider Configuration & Testing</p>
              </div>
            </div>

            {/* Test Result Banner */}
            {testResult && (
              <div
                className={`mb-6 p-4 rounded-lg border ${
                  testResult.success
                    ? 'bg-success/20 border-success'
                    : 'bg-danger/20 border-danger'
                }`}
              >
                <div className="flex items-start gap-3">
                  <span className="text-xl">{testResult.success ? '✓' : '✗'}</span>
                  <div className="flex-1">
                    <h3
                      className={`text-sm font-semibold mb-1 ${
                        testResult.success ? 'text-success' : 'text-danger'
                      }`}
                    >
                      {testResult.success ? 'Test Successful' : 'Test Failed'}
                    </h3>
                    <p
                      className={`text-sm ${
                        testResult.success ? 'text-success' : 'text-danger'
                      }`}
                    >
                      {testResult.message}
                    </p>
                    <div className="flex items-center gap-4 mt-2 text-xs text-muted">
                      <span>Latency: {testResult.latency}ms</span>
                      {testResult.model_used && (
                        <span>Model: {testResult.model_used}</span>
                      )}
                    </div>
                    {testResult.response && (
                      <div className="mt-3 p-3 bg-bg rounded border border-border">
                        <h4 className="text-xs font-semibold text-text mb-2">
                          Sample Response:
                        </h4>
                        <pre className="text-xs text-text whitespace-pre-wrap">
                          {testResult.response}
                        </pre>
                      </div>
                    )}
                  </div>
                  <button
                    onClick={() => setTestResult(null)}
                    className={
                      testResult.success
                        ? 'text-success hover:text-success/80'
                        : 'text-danger hover:text-danger/80'
                    }
                    aria-label="Dismiss"
                  >
                    ✕
                  </button>
                </div>
              </div>
            )}

            {/* Status Metrics */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
              <div className="bg-bg rounded-lg p-4">
                <div className="text-xs text-muted mb-1">Status</div>
                <div
                  className={`text-lg font-semibold ${
                    selectedProvider.enabled ? 'text-success' : 'text-muted'
                  }`}
                >
                  {selectedProvider.enabled ? 'Enabled' : 'Disabled'}
                </div>
              </div>
              <div className="bg-bg rounded-lg p-4">
                <div className="text-xs text-muted mb-1">Priority</div>
                <div className="text-lg font-semibold text-text">
                  {selectedProvider.priority || 'N/A'}
                </div>
              </div>
              <div className="bg-bg rounded-lg p-4">
                <div className="text-xs text-muted mb-1">Weight</div>
                <div className="text-lg font-semibold text-text">
                  {selectedProvider.weight || 1.0}
                </div>
              </div>
              <div className="bg-bg rounded-lg p-4">
                <div className="text-xs text-muted mb-1">Models</div>
                <div className="text-lg font-semibold text-text">
                  {selectedProvider.models?.length || 0}
                </div>
              </div>
            </div>

            {/* Priority Actions */}
            <div className="flex gap-2 mb-6">
              <button
                onClick={() =>
                  selectedProvider.id &&
                  handleSetPriority(selectedProvider.id, 1, 'primary')
                }
                className="px-4 py-2 bg-info text-text-inverse rounded-lg hover:bg-info/90 transition-colors text-sm font-medium shadow-glow-primary"
              >
                🏆 Set as Primary
              </button>
              <button
                onClick={() =>
                  selectedProvider.id &&
                  handleSetPriority(selectedProvider.id, 10, 'fallback')
                }
                className="px-4 py-2 bg-warning text-text-inverse rounded-lg hover:bg-warning/90 transition-colors text-sm font-medium"
              >
                🛡️ Set as Fallback
              </button>
            </div>

            {/* Configuration Details */}
            <div className="space-y-3">
              <div>
                <label
                  htmlFor="provider-base-url"
                  className="block text-xs font-medium text-text mb-1"
                >
                  Base URL
                </label>
                <input
                  id="provider-base-url"
                  type="text"
                  value={selectedProvider.base_url || 'Not configured'}
                  readOnly
                  className="w-full px-3 py-2 border border-border rounded-lg bg-surface-hover text-sm"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-text mb-1">
                  API Key Status
                </label>
                <div
                  className={`px-3 py-2 border rounded-lg text-sm ${
                    selectedProvider.api_key
                      ? 'border-success bg-success/20 text-success'
                      : 'border-danger bg-danger/20 text-danger'
                  }`}
                >
                  {selectedProvider.api_key ? '✓ Configured' : '✗ Not configured'}
                </div>
              </div>
            </div>
          </div>

          {/* Prompt Testing Panel */}
          <div className="bg-surface rounded-xl shadow-sm border border-border p-6">
            <h3 className="text-lg font-semibold text-text mb-4">
              Test with Custom Prompt
            </h3>
            <div className="space-y-4">
              <div>
                <label
                  htmlFor="test-prompt"
                  className="block text-sm font-medium text-text mb-2"
                >
                  Enter your test prompt:
                </label>
                <textarea
                  id="test-prompt"
                  value={testPrompt}
                  onChange={(e) => setTestPrompt(e.target.value)}
                  rows={4}
                  className="w-full px-3 py-2 border border-border rounded-lg focus:ring-2 focus:ring-primary focus:border-primary bg-bg text-text"
                  placeholder="e.g., Write a hello world program in Python"
                />
              </div>
              <button
                onClick={handlePromptTest}
                disabled={testing === selectedProvider.name || !testPrompt.trim()}
                className="w-full px-4 py-3 bg-success text-text-inverse rounded-lg hover:bg-success/90 disabled:bg-surface-hover disabled:cursor-not-allowed transition-colors text-sm font-medium flex items-center justify-center gap-2 shadow-glow-primary"
              >
                {testing === selectedProvider.name ? (
                  <>
                    <span className="animate-spin">🔄</span>
                    Testing with prompt...
                  </>
                ) : (
                  <>
                    <span>🧪</span>
                    Test API with Prompt
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Available Models */}
          {selectedProvider.models && selectedProvider.models.length > 0 && (
            <div className="bg-surface rounded-xl shadow-sm border border-border p-6">
              <h3 className="text-lg font-semibold text-text mb-4">
                Available Models ({selectedProvider.models.length})
              </h3>
              <div className="flex flex-wrap gap-2">
                {selectedProvider.models.map((model) => (
                  <span
                    key={model}
                    className="px-3 py-1.5 bg-primary/20 text-primary rounded-full text-sm font-medium"
                  >
                    {model}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      ) : (
        <div className="bg-surface rounded-xl shadow-sm border border-border p-12 text-center">
          <div className="text-6xl mb-4">🔌</div>
          <h3 className="text-lg font-medium text-text mb-2">
            Select a Provider
          </h3>
          <p className="text-muted">
            Choose a provider from the sidebar to test and configure
          </p>
        </div>
      )}
    </div>
  );

  return <TwoColumnLayout sidebar={sidebar}>{mainContent}</TwoColumnLayout>;
}
