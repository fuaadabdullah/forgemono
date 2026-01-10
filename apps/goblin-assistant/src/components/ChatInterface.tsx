import React, { useRef } from 'react';
import { useToast } from '../contexts/ToastContext';
import { useProvider } from '../contexts/ProviderContext';
import { useChatState } from '../hooks/useChatState';
import { useChatStreaming } from '../hooks/useChatStreaming';
import { ProviderSelector } from './chat/ProviderSelector';
import { MessageList } from './chat/MessageList';
import { ChatInput } from './chat/ChatInput';
import { ChatStats } from './chat/ChatStats';

interface ChatInterfaceProps {
  demoMode?: boolean;
}

export const ChatInterface: React.FC<ChatInterfaceProps> = ({ demoMode = false }) => {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const { showError } = useToast();
  const { selectedProvider, selectedModel, setSelectedProvider, setSelectedModel } = useProvider();

  // Use custom hooks for state management and streaming
  const {
    messages,
    totalCost,
    totalTokens,
    formatCost,
    formatTokens,
    addUserMessage,
    addAssistantMessage,
    updateMessage,
  } = useChatState();

  const { sendMessage, isLoading } = useChatStreaming({
    demoMode,
    selectedProvider,
    selectedModel,
    onMessageStart: (messageId) => {
      // Add placeholder assistant message with the ID from the hook
      addAssistantMessage('', { provider: selectedProvider, model: selectedModel, id: messageId });
    },
    onMessageUpdate: (messageId, content) => {
      updateMessage(messageId, { content });
    },
    onMessageComplete: (messageId, metadata) => {
      updateMessage(messageId, metadata);
    },
    onError: showError,
  });

  const handleSendMessage = async (message: string) => {
    if (!message.trim() || isLoading) return;

    // Add user message
    addUserMessage(message);

    // Start streaming response
    await sendMessage(message);
  };

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Header with Provider/Model Selection */}
        <ProviderSelector
          selectedProvider={selectedProvider}
          selectedModel={selectedModel}
          onProviderChange={setSelectedProvider}
          onModelChange={setSelectedModel}
          demoMode={demoMode}
        />

        {/* Messages Area */}
        <MessageList
          messages={messages}
          isLoading={isLoading}
          formatCost={formatCost}
          formatTokens={formatTokens}
          ref={messagesEndRef}
        />

        {/* Input Area */}
        <ChatInput onSendMessage={handleSendMessage} disabled={isLoading} ref={inputRef} />
      </div>

      {/* Statistics Sidebar */}
      <ChatStats
        totalCost={totalCost}
        totalTokens={totalTokens}
        messageCount={messages.length}
        recentMessages={messages}
        formatCost={formatCost}
        formatTokens={formatTokens}
        demoMode={demoMode}
      />
    </div>
  );
};
