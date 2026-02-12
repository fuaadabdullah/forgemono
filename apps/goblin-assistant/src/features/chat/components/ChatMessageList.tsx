import type { RefObject } from 'react';
import type { ChatMessage, QuickPrompt } from '../types';

interface ChatMessageListProps {
  /** Conversation messages in display order. */
  messages: ChatMessage[];
  /** Suggested prompts displayed when there are no messages. */
  quickPrompts: QuickPrompt[];
  /** Callback for clicking a quick prompt. */
  onPromptClick: (prompt: string) => void;
  /** Scroll anchor for auto-scrolling. */
  bottomRef: RefObject<HTMLDivElement>;
  /** Whether the assistant is currently responding. */
  isSending: boolean;
}

const ChatMessageList = ({
  messages,
  quickPrompts,
  onPromptClick,
  bottomRef,
  isSending,
}: ChatMessageListProps) => {
  if (messages.length === 0) {
    return (
      <section className="flex flex-col items-center justify-center h-full text-center">
        <div className="mb-6">
          <div className="w-16 h-16 bg-primary/20 rounded-full flex items-center justify-center mx-auto mb-4">
            <span className="text-3xl">🤖</span>
          </div>
          <h2 className="text-2xl font-semibold text-text mb-2">
            Welcome! What do you need help with?
          </h2>
          <p className="text-muted">
            Type a question or choose a suggestion to get started.
          </p>
        </div>
        <div className="flex flex-wrap justify-center gap-2">
          {quickPrompts.map(item => (
            <button
              key={item.label}
              onClick={() => onPromptClick(item.prompt)}
              className="px-3 py-2 rounded-full border border-border text-sm text-text hover:bg-surface-hover"
              type="button"
            >
              {item.label}
            </button>
          ))}
        </div>
        <div ref={bottomRef} aria-hidden="true" />
      </section>
    );
  }

  return (
    <section className="max-w-3xl mx-auto space-y-4" aria-label="Chat transcript">
      <ol
        role="log"
        aria-live="polite"
        aria-relevant="additions"
        aria-busy={isSending}
        className="space-y-4"
      >
        {messages.map((msg, idx) => {
          const isUser = msg.role === 'user';
          return (
            <li key={idx} className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-[80%] ${isUser ? 'text-right' : 'text-left'}`}>
                <div className="text-xs uppercase tracking-wide text-muted mb-1">
                  {isUser ? 'You' : 'Assistant'}
                </div>
                <div
                  className={`rounded-2xl px-4 py-3 leading-relaxed ${
                    isUser
                      ? 'bg-primary text-text-inverse shadow-glow-primary rounded-br-sm'
                      : 'bg-surface text-text border border-border rounded-bl-sm'
                  } whitespace-pre-wrap`}
                >
                  {msg.content}
                </div>
              </div>
            </li>
          );
        })}
      </ol>
      <div ref={bottomRef} aria-hidden="true" />
    </section>
  );
};

export default ChatMessageList;
