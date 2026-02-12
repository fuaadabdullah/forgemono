export type ChatRole = 'user' | 'assistant' | 'system';

export interface ChatMessage {
  role: ChatRole;
  content: string;
}

export interface ChatThread {
  id: string;
  title: string;
  snippet: string;
  createdAt: string;
  updatedAt: string;
}
