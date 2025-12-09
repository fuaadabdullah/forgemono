import React, { useState, useEffect, useRef } from 'react';
import { apiClient } from '../api/client-axios';
import TurnstileWidget from '../components/TurnstileWidget';
import { useTurnstile } from '../config/turnstile';

interface ChatMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
}

const ChatPage: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [isSending, setIsSending] = useState(false);
  const [totalTokens, setTotalTokens] = useState(0);
  const [turnstileToken, setTurnstileToken] = useState('');
  const bottomRef = useRef<HTMLDivElement | null>(null);

  const turnstileConfig = useTurnstile('chat');

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim() || isSending) return;

    // Check for Turnstile token (optional for now, can be enforced later)
    if (!turnstileToken) {
      console.warn('No Turnstile token available, proceeding without bot protection');
    }

    setIsSending(true);

    const userMsg: ChatMessage = { role: 'user', content: input.trim() };
    setMessages((prev) => [...prev, userMsg]);
    setInput('');

    try {
      const completion = await apiClient.chatCompletion([...messages, userMsg], undefined, undefined, turnstileToken);
      const answer = completion?.choices?.[0]?.message?.content || completion?.content || 'No response';
      setMessages((prev) => [...prev, { role: 'assistant', content: answer }]);
      setTotalTokens((prev) => prev + (completion?.usage?.total_tokens || 0));
    } catch (err: any) {
      setMessages((prev) => [...prev, { role: 'assistant', content: `Error: ${err.message}` }]);
    } finally {
      setIsSending(false);
      // Reset Turnstile token after use
      setTurnstileToken('');
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="flex h-[calc(100vh-64px)]">
      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col bg-bg">
        <div className="flex-1 overflow-y-auto px-4 py-8">
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-center">
              <div className="mb-6">
                <div className="w-16 h-16 bg-primary/20 rounded-full flex items-center justify-center mx-auto mb-4">
                  <span className="text-3xl">🤖</span>
                </div>
                <h2 className="text-2xl font-semibold text-text mb-2">Welcome to Goblin Assistant!</h2>
                <p className="text-muted">Start a conversation by typing a message below.</p>
              </div>
            </div>
          ) : (
            <div className="max-w-3xl mx-auto space-y-4">
              {messages.map((msg, idx) => (
                <div
                  key={idx}
                  className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-[70%] rounded-lg px-4 py-3 ${
                      msg.role === 'user'
                        ? 'bg-primary text-text-inverse shadow-glow-primary'
                        : 'bg-surface text-text border border-border'
                    }`}
                  >
                    {msg.content}
                  </div>
                </div>
              ))}
              <div ref={bottomRef} />
            </div>
          )}
        </div>

        {/* Input Area */}
        <div className="border-t border-border bg-surface px-4 py-4">
          <div className="max-w-3xl mx-auto flex items-center space-x-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Type your message..."
              className="flex-1 px-4 py-3 border border-border bg-surface-hover rounded-lg focus:outline-none focus:ring-2 focus:ring-primary text-text placeholder-muted"
              disabled={isSending}
              aria-label="Chat message input"
            />
            <button
              onClick={sendMessage}
              disabled={isSending || !input.trim()}
              className="bg-primary hover:brightness-110 disabled:opacity-50 text-text-inverse px-6 py-3 rounded-lg font-medium shadow-glow-primary transition-all"
            >
              {isSending ? '⏳' : '📤'}
            </button>
          </div>
          <p className="text-xs text-muted text-center mt-2">Press Enter to send, Shift+Enter for new line</p>
        </div>
      </div>

      {/* Stats Sidebar */}
      <div className="w-80 border-l border-border bg-surface p-6">
        <div className="space-y-6">
          <div>
            <h3 className="text-sm font-medium text-muted mb-2">Total Cost</h3>
            <p className="text-2xl font-semibold text-success">$0.0000</p>
          </div>
          <div>
            <h3 className="text-sm font-medium text-muted mb-2">Total Tokens</h3>
            <p className="text-2xl font-semibold text-text">{totalTokens}</p>
          </div>
          <div>
            <h3 className="text-sm font-medium text-muted mb-2">Messages</h3>
            <p className="text-2xl font-semibold text-text">{messages.length}</p>
          </div>
        </div>
      </div>

      {/* Invisible Turnstile Widget for API Protection */}
      <div style={{ position: 'absolute', opacity: 0, pointerEvents: 'none' }}>
        <TurnstileWidget
          siteKey={turnstileConfig.siteKey}
          onVerify={(token) => setTurnstileToken(token)}
          mode="invisible"
          onError={(error) => {
            console.error('Turnstile error:', error);
          }}
        />
      </div>
    </div>
  );
};

export default ChatPage;
