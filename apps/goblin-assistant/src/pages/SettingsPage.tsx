import React from 'react';
import { useProviderSettings } from '../hooks/api/useSettings';
import ThemePreview from '../components/ThemePreview';
import KeyboardShortcutsHelp from '../components/KeyboardShortcutsHelp';



const SettingsPage: React.FC = () => {
    const { data: providerData, isLoading: providersLoading } = useProviderSettings();
  // Adapt provider data shape: backend may return keys with different naming (configured/env_var)
  const providers = (providerData || []).map((p: any) => ({
    name: p.name,
    configured: p.enabled ?? p.configured ?? false,
    env_var: p.env_var || p.api_key ? `${p.name.toUpperCase()}_API_KEY` : undefined,
    models: p.models || [],
  }));
  const loading = providersLoading;

  if (loading) {
    return (
      <div className="min-h-screen bg-bg flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin text-4xl mb-4">🔄</div>
          <p className="text-muted">Loading settings...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-bg py-12 px-4">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-12">
          <h1 className="text-4xl font-bold text-primary mb-3">Provider & Model Settings</h1>
          <p className="text-muted">
            Configure your AI provider API keys and model preferences
          </p>
        </div>

        {/* Theme Preview + Palette Switcher */}
        <div className="mb-10">
          <ThemePreview />
        </div>

        {/* Keyboard Shortcuts */}
        <div className="mb-10">
          <KeyboardShortcutsHelp />
        </div>

        {/* Environment Variables Instructions */}
        <div className="bg-surface rounded-xl shadow-sm border border-border p-6 mb-8">
          <h2 className="text-xl font-semibold text-text mb-4">How to Configure API Keys</h2>
          <div className="space-y-3 text-text">
            <p>
              API keys should be set as environment variables on the backend server.
            </p>
            <div className="bg-bg rounded-lg p-4 font-mono text-sm text-primary">
              <div>export OPENAI_API_KEY="your-key-here"</div>
              <div>export ANTHROPIC_API_KEY="your-key-here"</div>
              <div>export GROQ_API_KEY="your-key-here"</div>
              <div>export GOOGLE_API_KEY="your-key-here"</div>
            </div>
            <p className="text-sm text-muted">
              For persistent configuration, add these to your <code className="bg-surface-hover px-2 py-1 rounded text-primary">.env</code> file or shell profile.
            </p>
          </div>
        </div>

        {/* Provider Status Cards */}
        <div>
          <h2 className="text-2xl font-semibold text-text mb-6">Provider Status</h2>
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {providers.map((provider: { name: string; configured: boolean; env_var?: string; models?: string[] }) => (
              <div
                key={provider.name}
                className="bg-surface rounded-lg shadow-sm border border-border p-6 hover:shadow-md transition-shadow"
              >
                {/* Provider Header */}
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-text">{provider.name}</h3>
                  <span
                    className={`px-3 py-1 rounded-full text-xs font-medium ${
                      provider.configured
                        ? 'bg-success/20 text-success'
                        : 'bg-danger/20 text-danger'
                    }`}
                  >
                    {provider.configured ? 'Configured' : 'Missing'}
                  </span>
                </div>

                {/* Provider Icon */}
                <div className="flex items-center justify-center w-16 h-16 bg-surface-hover rounded-lg mb-4 mx-auto">
                  <span className="text-3xl">
                    {provider.name === 'OpenAI' && '🤖'}
                    {provider.name === 'Anthropic' && '🧠'}
                    {provider.name === 'Groq' && '⚡'}
                    {provider.name === 'Google' && '🔍'}
                    {provider.name === 'Cohere' && '💬'}
                    {provider.name === 'Together' && '🤝'}
                    {!['OpenAI', 'Anthropic', 'Groq', 'Google', 'Cohere', 'Together'].includes(provider.name) && '🔧'}
                  </span>
                </div>

                {/* Environment Variable */}
                {provider.env_var && (
                  <div className="mb-4">
                    <p className="text-xs text-muted mb-1">Environment Variable:</p>
                    <code className="block bg-bg px-3 py-2 rounded text-xs font-mono text-primary break-all">
                      {provider.env_var}
                    </code>
                  </div>
                )}

                {/* Models */}
                {provider.models && provider.models.length > 0 && (
                  <div>
                    <p className="text-xs text-muted mb-2">Available Models:</p>
                    <div className="flex flex-wrap gap-1">
                      {provider.models.map((model: string) => (
                        <span
                          key={model}
                          className="inline-block bg-primary/20 text-primary px-2 py-1 rounded text-xs font-medium"
                        >
                          {model}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Status Message */}
                <div className="mt-4 pt-4 border-t border-border">
                  <p className={`text-xs ${provider.configured ? 'text-success' : 'text-danger'}`}>
                    {provider.configured
                      ? '✓ API key detected and ready to use'
                      : '✗ API key not found. Configure on backend.'}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Additional Settings Placeholder */}
        <div className="mt-12 bg-surface rounded-xl shadow-sm border border-border p-6">
          <h2 className="text-xl font-semibold text-text mb-4">Model Preferences</h2>
          <p className="text-muted mb-4">
            Configure default model settings and routing preferences.
          </p>
          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <label htmlFor="default-provider" className="block text-sm font-medium text-text mb-2">
                Default Provider
              </label>
              <select id="default-provider" className="w-full px-4 py-2 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary bg-surface-hover text-text">
                <option>OpenAI</option>
                <option>Anthropic</option>
                <option>Groq</option>
                <option>Google</option>
              </select>
            </div>
            <div>
              <label htmlFor="default-model" className="block text-sm font-medium text-text mb-2">
                Default Model
              </label>
              <select id="default-model" className="w-full px-4 py-2 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary bg-surface-hover text-text">
                <option>gpt-4-turbo</option>
                <option>claude-3-opus</option>
                <option>llama-3-70b</option>
                <option>gemini-pro</option>
              </select>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SettingsPage;
