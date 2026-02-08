import type { ChatMessage, ChatThread } from '../domain/chat';

export const CHAT_THREADS_STORAGE_KEY = 'goblin_chat_threads_v1';
export const CHAT_MESSAGES_STORAGE_PREFIX = 'goblin_chat_messages_v1';
const CHAT_PRELOAD_STORAGE_KEY = 'goblin_preload_chat_v1';

export const sortChatThreads = (threads: ChatThread[]) =>
  [...threads].sort(
    (a, b) => new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime()
  );

export const readChatThreads = (): ChatThread[] => {
  if (typeof window === 'undefined') return [];
  try {
    const raw = window.localStorage.getItem(CHAT_THREADS_STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) return [];
    return sortChatThreads(parsed.filter(Boolean) as ChatThread[]);
  } catch (error) {
    console.warn('Failed to read chat threads from storage:', error);
    return [];
  }
};

export const writeChatThreads = (threads: ChatThread[]): void => {
  if (typeof window === 'undefined') return;
  try {
    window.localStorage.setItem(CHAT_THREADS_STORAGE_KEY, JSON.stringify(threads));
  } catch (error) {
    console.warn('Failed to persist chat threads:', error);
  }
};

const messagesKey = (conversationId: string) =>
  `${CHAT_MESSAGES_STORAGE_PREFIX}:${conversationId}`;

export const readChatMessages = (conversationId: string): ChatMessage[] => {
  if (typeof window === 'undefined') return [];
  try {
    const raw = window.localStorage.getItem(messagesKey(conversationId));
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) return [];
    return parsed as ChatMessage[];
  } catch (error) {
    console.warn('Failed to read chat messages:', error);
    return [];
  }
};

export const writeChatMessages = (
  conversationId: string,
  nextMessages: ChatMessage[]
): void => {
  if (typeof window === 'undefined') return;
  try {
    window.localStorage.setItem(messagesKey(conversationId), JSON.stringify(nextMessages));
  } catch (error) {
    console.warn('Failed to persist chat messages:', error);
  }
};

export const preloadRecentChat = (limit = 5): { threadId: string; messages: ChatMessage[] } | null => {
  if (typeof window === 'undefined') return null;
  const threads = readChatThreads();
  if (threads.length === 0) return null;
  const thread = threads[0];
  const messages = readChatMessages(thread.id).slice(-limit);
  const payload = {
    threadId: thread.id,
    messages,
    timestamp: new Date().toISOString(),
  };
  try {
    window.sessionStorage.setItem(CHAT_PRELOAD_STORAGE_KEY, JSON.stringify(payload));
  } catch (error) {
    console.warn('Failed to store preloaded chat messages:', error);
  }
  return { threadId: thread.id, messages };
};

export const readPreloadedChat = (): { threadId: string; messages: ChatMessage[] } | null => {
  if (typeof window === 'undefined') return null;
  try {
    const raw = window.sessionStorage.getItem(CHAT_PRELOAD_STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    if (!parsed || typeof parsed !== 'object') return null;
    if (!Array.isArray(parsed.messages)) return null;
    return { threadId: parsed.threadId as string, messages: parsed.messages as ChatMessage[] };
  } catch (error) {
    console.warn('Failed to read preloaded chat messages:', error);
    return null;
  }
};

export const clearPreloadedChat = (): void => {
  if (typeof window === 'undefined') return;
  try {
    window.sessionStorage.removeItem(CHAT_PRELOAD_STORAGE_KEY);
  } catch (error) {
    console.warn('Failed to clear preloaded chat messages:', error);
  }
};
