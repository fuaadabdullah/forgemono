import { useState } from 'react';
import { runtimeClient, runtimeClientDemo } from '../lib/api/api-client';
import { useToast } from '../contexts/ToastContext';

interface UseChatStreamingOptions {
  demoMode?: boolean;
  selectedProvider?: string;
  selectedModel?: string;
  onMessageStart?: (messageId: string) => void;
  onMessageUpdate?: (messageId: string, content: string) => void;
  onMessageComplete?: (
    messageId: string,
    metadata: {
      cost: number;
      tokens: number;
      provider?: string;
      model?: string;
    }
  ) => void;
  onError?: (error: string) => void;
}

/**
 * Custom hook for handling chat message streaming
 * @param options Configuration options for streaming behavior
 * @returns Streaming state and send message function
 */
export function useChatStreaming(options: UseChatStreamingOptions) {
  const [isLoading, setIsLoading] = useState(false);
  const { showError } = useToast();

  const {
    demoMode = false,
    selectedProvider,
    selectedModel,
    onMessageStart,
    onMessageUpdate,
    onMessageComplete,
    onError,
  } = options;

  // Get the appropriate runtime client
  const getRuntimeClient = () => (demoMode ? runtimeClientDemo : runtimeClient);

  const sendMessage = async (message: string) => {
    if (!message.trim() || isLoading) return;

    setIsLoading(true);

    try {
      const client = getRuntimeClient();

      let responseContent = '';
      let messageCost = 0;
      let messageTokens = 0;

      // Create a temporary message ID for streaming updates
      const messageId = Date.now().toString();
      onMessageStart?.(messageId);

      await client.executeTaskStreaming(
        'docs-writer',
        message.trim(),
        (chunk) => {
          if (chunk.chunk) {
            responseContent += chunk.chunk;
            onMessageUpdate?.(messageId, responseContent);
          }
          if (typeof chunk.cost_delta === 'number') {
            messageCost += chunk.cost_delta;
          }
          if (typeof chunk.token_count === 'number') {
            messageTokens += chunk.token_count;
          }
        },
        (response) => {
          if (typeof response.cost === 'number') messageCost = response.cost;
          if (response.model) {
            messageTokens =
              response.model === 'demo-model'
                ? Math.floor(responseContent.length / 4)
                : messageTokens;
          }

          onMessageComplete?.(messageId, {
            cost: messageCost,
            tokens: messageTokens,
            provider: selectedProvider,
            model: selectedModel,
          });
        },
        undefined, // code
        selectedProvider,
        selectedModel
      );
    } catch (error) {
      console.error('Failed to send message:', error);
      const errorMessage = error instanceof Error ? error.message : 'An unexpected error occurred';
      showError('Message Failed', errorMessage);
      onError?.(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  return {
    isLoading,
    sendMessage,
  };
}
