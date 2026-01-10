import { useState, useEffect } from 'react';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { runtimeClient, runtimeClientDemo } from '../../lib/api/api-client';
import { useToast } from '../../contexts/ToastContext';

interface ProviderSelectorProps {
  selectedProvider?: string;
  selectedModel?: string;
  onProviderChange: (provider: string) => void;
  onModelChange: (model: string) => void;
  demoMode?: boolean;
}

/**
 * Provider and model selection component
 */
export function ProviderSelector({
  selectedProvider,
  selectedModel,
  onProviderChange,
  onModelChange,
  demoMode = false,
}: ProviderSelectorProps) {
  const [providers, setProviders] = useState<string[]>([]);
  const [models, setModels] = useState<string[]>([]);
  const [loadingProviders, setLoadingProviders] = useState(true);
  const [loadingModels, setLoadingModels] = useState(false);

  const { showError } = useToast();

  // Get the appropriate runtime client
  const getRuntimeClient = () => (demoMode ? runtimeClientDemo : runtimeClient);

  // Load providers on mount
  useEffect(() => {
    const loadProviders = async () => {
      try {
        setLoadingProviders(true);
        const client = getRuntimeClient();
        const providerList = await client.getProviders();
        setProviders(providerList);
        if (providerList.length > 0 && !selectedProvider) {
          onProviderChange(providerList[0]);
        }
      } catch (error) {
        console.error('Failed to load providers:', error);
        showError(
          'Failed to Load Providers',
          'Unable to connect to the server. Please check your connection and try again.'
        );
      } finally {
        setLoadingProviders(false);
      }
    };
    loadProviders();
  }, [demoMode, selectedProvider, onProviderChange, showError]);

  // Load models when provider changes
  useEffect(() => {
    const loadModels = async () => {
      if (!selectedProvider) return;

      try {
        setLoadingModels(true);
        const client = getRuntimeClient();
        const modelList = await client.getProviderModels(selectedProvider);
        setModels(modelList);
        if (modelList.length > 0 && !selectedModel) {
          onModelChange(modelList[0]);
        }
      } catch (error) {
        console.error('Failed to load models:', error);
        showError(
          'Failed to Load Models',
          `Unable to load models for ${selectedProvider}. Please try selecting a different provider.`
        );
      } finally {
        setLoadingModels(false);
      }
    };
    loadModels();
  }, [selectedProvider, selectedModel, onModelChange, demoMode, showError]);

  return (
    <div className="flex items-center space-x-2">
      <Select value={selectedProvider} onValueChange={onProviderChange} disabled={loadingProviders}>
        <SelectTrigger className="w-32">
          <SelectValue placeholder={loadingProviders ? 'Loading...' : 'Provider'} />
        </SelectTrigger>
        <SelectContent>
          {providers.map((provider) => (
            <SelectItem key={provider} value={provider}>
              {provider}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      <Select
        value={selectedModel}
        onValueChange={onModelChange}
        disabled={loadingModels || !selectedProvider}
      >
        <SelectTrigger className="w-40">
          <SelectValue placeholder={loadingModels ? 'Loading...' : 'Model'} />
        </SelectTrigger>
        <SelectContent>
          {models.map((model) => (
            <SelectItem key={model} value={model}>
              {model}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
}
