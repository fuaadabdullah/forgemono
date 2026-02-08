import { useState } from 'react';
import { apiClient } from '../api/apiClient';

interface UseChatStreamingOptions {
  demoMode?: boolean;
  selectedProvider?: string;
  selectedModel?: string;
  onMessageStart?: (messageId: string) => void;
  onMessageUpdate?: (messageId: string, content: string) => void;
  onMessageComplete?: (messageId: string, metadata: Record<string, unknown>) => void;
  onError?: (title: string, message?: string) => void;
}

const createMessageId = () => {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID();
  }
  return `${Date.now()}-${Math.random().toString(16).slice(2)}`;
};

export const useChatStreaming = ({
  demoMode = false,
  selectedProvider,
  selectedModel,
  onMessageStart,
  onMessageUpdate,
  onMessageComplete,
  onError,
}: UseChatStreamingOptions) => {
  const [isLoading, setIsLoading] = useState(false);

  const sendMessage = async (message: string) => {
    const messageId = createMessageId();
    onMessageStart?.(messageId);
    setIsLoading(true);

    try {
      const response = await apiClient.chatCompletion(
        [{ role: 'user', content: message }],
        selectedModel,
        true
      );

      const content =
        typeof response === 'string'
          ? response
          : (response as { content?: string })?.content || JSON.stringify(response);

      onMessageUpdate?.(messageId, content);
      onMessageComplete?.(messageId, {
        content,
        provider: selectedProvider,
        model: selectedModel,
        demoMode,
      });
    } catch (error) {
      const messageText = error instanceof Error ? error.message : 'Failed to send message';
      onError?.('Chat error', messageText);
    } finally {
      setIsLoading(false);
    }
  };

  return { sendMessage, isLoading };
};
