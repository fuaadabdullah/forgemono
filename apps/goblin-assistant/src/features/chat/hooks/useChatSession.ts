import type { KeyboardEvent, RefObject } from 'react';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { chatClient } from '../api';
import { toUiError } from '../../../lib/ui-error';
import type { ChatMessage, ChatThread, QuickPrompt } from '../types';
import { useChatThreads } from './useChatThreads';
import { readChatMessages, writeChatMessages } from '../../../lib/chat-history';
import { CHAT_QUICK_PROMPTS } from '../../../content/brand';

export interface ChatSessionState {
  messages: ChatMessage[];
  input: string;
  isSending: boolean;
  totalTokens: number;
  quickPrompts: QuickPrompt[];
  threads: ChatThread[];
  isThreadsLoading: boolean;
  activeThreadId: string | null;
  inputRef: RefObject<HTMLTextAreaElement>;
  bottomRef: RefObject<HTMLDivElement>;
  setInput: (value: string) => void;
  sendMessage: (messageOverride?: string) => Promise<void>;
  selectThread: (threadId: string) => void;
  handleClearChat: () => void;
  handlePromptClick: (prompt: string) => void;
  handleKeyDown: (e: KeyboardEvent<HTMLTextAreaElement>) => void;
}

export const useChatSession = (): ChatSessionState => {
  const { threads, isLoading: isThreadsLoading, upsertThread } = useChatThreads();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [isSending, setIsSending] = useState(false);
  const [totalTokens, setTotalTokens] = useState(0);
  const [activeThreadId, setActiveThreadId] = useState<string | null>(null);
  const inputRef = useRef<HTMLTextAreaElement | null>(null);
  const bottomRef = useRef<HTMLDivElement | null>(null);
  const hasHydratedRef = useRef(false);

  const quickPrompts = useMemo<QuickPrompt[]>(
    () => CHAT_QUICK_PROMPTS.map(item => ({ label: item.label, prompt: item.prompt })),
    []
  );

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    if (hasHydratedRef.current) return;
    if (activeThreadId) {
      hasHydratedRef.current = true;
      return;
    }
    if (threads.length > 0) {
      const mostRecent = threads[0];
      setActiveThreadId(mostRecent.id);
      setMessages(readChatMessages(mostRecent.id));
      hasHydratedRef.current = true;
    }
  }, [activeThreadId, threads]);

  const selectThread = useCallback((threadId: string) => {
    setActiveThreadId(threadId);
    setMessages(readChatMessages(threadId));
    setTotalTokens(0);
    setInput('');
    hasHydratedRef.current = true;
    inputRef.current?.focus();
  }, []);

  const sendMessage = useCallback(
    async (messageOverride?: string) => {
      const content = (messageOverride ?? input).trim();
      if (!content || isSending) return;

      setIsSending(true);

      const userMsg: ChatMessage = { role: 'user', content };
      const updatedMessages = [...messages, userMsg];
      setMessages(updatedMessages);
      setInput('');

      try {
        let conversationId = activeThreadId;
        let createdAt: string | undefined;

        if (!conversationId) {
          const created = await chatClient.createConversation({
            title: content.slice(0, 48),
          });
          conversationId = created.conversationId;
          createdAt = created.createdAt;
          setActiveThreadId(conversationId);
          upsertThread({
            id: conversationId,
            title: created.title ?? content.slice(0, 48),
            snippet: content,
            createdAt,
          });
        }

        if (!conversationId) {
          throw new Error('Conversation ID unavailable.');
        }

        writeChatMessages(conversationId, updatedMessages);

        // Send structured messages (not a flattened "User:/Assistant:" transcript).
        // Flattened transcripts frequently cause models to roleplay both sides and can balloon latency.
        const messagesForModel = updatedMessages.slice(-20);

        const result = await chatClient.sendMessage({
          conversationId,
          messages: messagesForModel,
        });
        const answer = result?.content || 'No response';
        setMessages(prev => {
          const assistantMsg: ChatMessage = { role: 'assistant', content: answer };
          const next = [...prev, assistantMsg];
          writeChatMessages(conversationId, next);
          return next;
        });
        setTotalTokens(prev => prev + (result?.usage?.total_tokens || 0));
        upsertThread({
          id: conversationId,
          snippet: answer,
          updatedAt: new Date().toISOString(),
        });
      } catch (err: unknown) {
        const uiError = toUiError(err, {
          code: 'CHAT_SEND_FAILED',
          userMessage: 'Sorry, we could not send that message right now.',
        });
        const assistantMsg: ChatMessage = { role: 'assistant', content: uiError.userMessage };
        setMessages(prev => [...prev, assistantMsg]);
      } finally {
        setIsSending(false);
        inputRef.current?.focus();
      }
    },
    [activeThreadId, input, isSending, messages, upsertThread]
  );

  const handleClearChat = useCallback(() => {
    setMessages([]);
    setTotalTokens(0);
    setInput('');
    setActiveThreadId(null);
    hasHydratedRef.current = true;
    inputRef.current?.focus();
  }, []);

  const handlePromptClick = useCallback((prompt: string) => {
    setInput(prompt);
    inputRef.current?.focus();
  }, []);

  const handleKeyDown = useCallback(
    (e: KeyboardEvent<HTMLTextAreaElement>) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
      }
    },
    [sendMessage]
  );

  return {
    messages,
    input,
    isSending,
    totalTokens,
    quickPrompts,
    threads,
    isThreadsLoading,
    activeThreadId,
    inputRef,
    bottomRef,
    setInput,
    sendMessage,
    selectThread,
    handleClearChat,
    handlePromptClick,
    handleKeyDown,
  };
};
