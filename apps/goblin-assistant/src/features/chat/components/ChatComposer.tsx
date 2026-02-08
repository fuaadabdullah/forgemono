import type { KeyboardEvent, RefObject } from 'react';
import type { QuickPrompt } from '../types';
import { CHAT_COMPOSER_PLACEHOLDER, CHAT_COMPOSER_TIP } from '../../../content/brand';

interface ChatComposerProps {
  /** Current input value. */
  input: string;
  /** Input ref for focusing. */
  inputRef: RefObject<HTMLTextAreaElement>;
  /** Whether a message is being sent. */
  isSending: boolean;
  /** Inline prompts shown beneath the composer. */
  quickPrompts: QuickPrompt[];
  /** Update input value. */
  onInputChange: (value: string) => void;
  /** Clear the current chat. */
  onClear: () => void;
  /** Send the message. */
  onSend: () => void;
  /** Keyboard handler for Enter/Shift+Enter. */
  onKeyDown: (e: KeyboardEvent<HTMLTextAreaElement>) => void;
  /** Handler for quick prompt selection. */
  onPromptClick: (prompt: string) => void;
}

const ChatComposer = ({
  input,
  inputRef,
  isSending,
  quickPrompts,
  onInputChange,
  onClear,
  onSend,
  onKeyDown,
  onPromptClick,
}: ChatComposerProps) => (
  <div className="border-t border-border bg-surface px-4 py-4">
    <div className="max-w-3xl mx-auto">
      <div className="bg-surface-hover border border-border rounded-2xl p-4">
        <label htmlFor="chat-input" className="sr-only">
          Message
        </label>
        <textarea
          id="chat-input"
          ref={inputRef}
          value={input}
          onChange={e => onInputChange(e.target.value)}
          onKeyDown={onKeyDown}
          placeholder={CHAT_COMPOSER_PLACEHOLDER}
          rows={3}
          className="w-full px-3 py-2 bg-transparent focus:outline-none text-text placeholder-muted resize-none min-h-[96px]"
          disabled={isSending}
          aria-label="Chat message input"
        />
        <div className="flex flex-wrap items-center justify-between gap-3 mt-3">
          <div className="text-xs text-muted">
            Tip: {CHAT_COMPOSER_TIP}
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={onClear}
              className="px-3 py-2 rounded-lg text-sm font-medium border border-border text-text hover:bg-surface-active"
              type="button"
            >
              Clear
            </button>
            <button
              onClick={onSend}
              disabled={isSending || !input.trim()}
              className="bg-primary hover:brightness-110 disabled:opacity-50 text-text-inverse px-4 py-2 rounded-lg font-medium shadow-glow-primary transition-all"
              type="button"
            >
              {isSending ? 'Sending...' : 'Send'}
            </button>
          </div>
        </div>
      </div>

      <div className="mt-3 flex flex-wrap gap-2">
        {quickPrompts.slice(0, 3).map(item => (
          <button
            key={`inline-${item.label}`}
            onClick={() => onPromptClick(item.prompt)}
            className="px-3 py-2 rounded-full border border-border text-xs text-text hover:bg-surface-hover"
            type="button"
          >
            {item.label}
          </button>
        ))}
      </div>

      <p className="text-xs text-muted text-center mt-2">
        Press Enter to send, Shift+Enter for new line
      </p>
    </div>
  </div>
);

export default ChatComposer;
