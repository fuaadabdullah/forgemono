import { forwardRef } from 'react';
import { Bot, User } from 'lucide-react';
import type { Message } from '../../hooks/useChatState';

interface MessageListProps {
  messages: Message[];
  isLoading?: boolean;
  formatCost: (cost: number) => string;
  formatTokens: (tokens: number) => string;
}

/**
 * Message list component for displaying chat messages
 */
export const MessageList = forwardRef<HTMLDivElement, MessageListProps>(
  ({ messages, isLoading, formatCost, formatTokens }, ref) => {
    return (
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="text-center text-gray-500 mt-8">
            <Bot className="w-12 h-12 mx-auto mb-4 text-gray-400" />
            <h3 className="text-lg font-medium mb-2">Welcome to Goblin Assistant!</h3>
            <p>Start a conversation by typing a message below.</p>
          </div>
        )}

        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                message.role === 'user'
                  ? 'bg-blue-600 text-white'
                  : 'bg-white border border-gray-200 text-gray-900'
              }`}
            >
              <div className="flex items-center mb-1">
                {message.role === 'user' ? (
                  <User className="w-4 h-4 mr-1" />
                ) : (
                  <Bot className="w-4 h-4 mr-1" />
                )}
                <span className="text-xs opacity-75">{message.timestamp.toLocaleTimeString()}</span>
              </div>
              <p className="text-sm whitespace-pre-wrap">{message.content}</p>
              {message.role === 'assistant' && message.cost && (
                <div className="flex items-center justify-between mt-2 pt-2 border-t border-gray-200 text-xs opacity-75">
                  <span>
                    {message.provider} • {message.model}
                  </span>
                  <div className="flex items-center space-x-2">
                    <span>{formatCost(message.cost)}</span>
                    <span>{formatTokens(message.tokens || 0)} tokens</span>
                  </div>
                </div>
              )}
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-white border border-gray-200 px-4 py-2 rounded-lg">
              <div className="flex items-center space-x-2">
                <Bot className="w-4 h-4" />
                <div className="flex space-x-1">
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:0.1s]"></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:0.2s]"></div>
                </div>
              </div>
            </div>
          </div>
        )}

        <div ref={ref} />
      </div>
    );
  }
);

MessageList.displayName = 'MessageList';
