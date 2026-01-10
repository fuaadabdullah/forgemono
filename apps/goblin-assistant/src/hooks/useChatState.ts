import { useState, useRef, useEffect } from 'react';

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  cost?: number;
  tokens?: number;
  provider?: string;
  model?: string;
}

/**
 * Custom hook for managing chat state including messages, costs, and tokens
 * @returns Chat state and state management functions
 */
export function useChatState() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [totalCost, setTotalCost] = useState(0);
  const [totalTokens, setTotalTokens] = useState(0);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const addMessage = (message: Omit<Message, 'id' | 'timestamp'>) => {
    const newMessage: Message = {
      ...message,
      id: Date.now().toString(),
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, newMessage]);
    return newMessage.id;
  };

  const updateMessage = (id: string, updates: Partial<Message>) => {
    setMessages((prev) => prev.map((msg) => (msg.id === id ? { ...msg, ...updates } : msg)));
  };

  const addUserMessage = (content: string) => {
    return addMessage({
      role: 'user',
      content: content.trim(),
    });
  };

  const addAssistantMessage = (
    content: string,
    metadata?: {
      cost?: number;
      tokens?: number;
      provider?: string;
      model?: string;
      id?: string;
    }
  ) => {
    const messageData = {
      role: 'assistant' as const,
      content,
      ...metadata,
    };

    if (metadata?.id) {
      // If ID is provided, create message with specific ID
      const newMessage: Message = {
        ...messageData,
        id: metadata.id,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, newMessage]);
      // Update totals
      if (metadata && metadata.cost !== undefined) {
        setTotalCost((prev) => prev + metadata.cost);
      }
      if (metadata && metadata.tokens !== undefined) {
        setTotalTokens((prev) => prev + metadata.tokens);
      }
      return metadata.id;
    } else {
      // Use the regular addMessage function
      return addMessage(messageData);
    }
  };

  const addErrorMessage = (errorMessage: string) => {
    return addMessage({
      role: 'assistant',
      content: `Sorry, I encountered an error: ${errorMessage}. Please try again.`,
    });
  };

  const clearMessages = () => {
    setMessages([]);
    setTotalCost(0);
    setTotalTokens(0);
  };

  const formatCost = (cost: number) => `$${cost.toFixed(4)}`;
  const formatTokens = (tokens: number) => tokens.toLocaleString();

  return {
    messages,
    totalCost,
    totalTokens,
    messagesEndRef,
    addUserMessage,
    addAssistantMessage,
    addErrorMessage,
    updateMessage,
    clearMessages,
    formatCost,
    formatTokens,
  };
}
