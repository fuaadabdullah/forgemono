import { Badge } from '../ui/badge';
import { DollarSign, Zap } from 'lucide-react';
import type { Message } from '../../hooks/useChatState';

interface ChatStatsProps {
  totalCost: number;
  totalTokens: number;
  messageCount: number;
  recentMessages: Message[];
  formatCost: (cost: number) => string;
  formatTokens: (tokens: number) => string;
  demoMode?: boolean;
}

/**
 * Chat statistics sidebar component
 */
export function ChatStats({
  totalCost,
  totalTokens,
  messageCount,
  recentMessages,
  formatCost,
  formatTokens,
  demoMode = false,
}: ChatStatsProps) {
  return (
    <div className="w-80 bg-white border-l border-gray-200 p-4">
      <div className="bg-white rounded-lg border border-gray-200 p-4">
        <div className="mb-4">
          <h3 className="text-lg font-semibold flex items-center mb-4">
            <DollarSign className="w-5 h-5 mr-2" />
            Session Stats
          </h3>

          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Total Cost</span>
              <span className="font-semibold text-green-600">{formatCost(totalCost)}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Total Tokens</span>
              <span className="font-semibold">{formatTokens(totalTokens)}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Messages</span>
              <span className="font-semibold">{messageCount}</span>
            </div>
          </div>
        </div>

        {messageCount > 0 && (
          <>
            <hr className="my-4" />
            <div>
              <h4 className="text-sm font-medium text-gray-900 mb-2">Recent Messages</h4>
              <div className="space-y-2 max-h-40 overflow-y-auto">
                {recentMessages.slice(-3).map((message) => (
                  <div key={message.id} className="text-xs text-gray-600">
                    <div className="flex items-center space-x-1">
                      <span
                        className={`w-3 h-3 rounded-full ${
                          message.role === 'user' ? 'bg-blue-500' : 'bg-green-500'
                        }`}
                      />
                      <span className="truncate flex-1">{message.content.substring(0, 30)}...</span>
                      {message.cost && (
                        <span className="text-green-600 ml-1">{formatCost(message.cost)}</span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </>
        )}

        {demoMode && (
          <div className="mt-4 pt-4 border-t border-gray-200">
            <Badge variant="secondary" className="text-xs">
              Demo Mode
            </Badge>
          </div>
        )}
      </div>
    </div>
  );
}
