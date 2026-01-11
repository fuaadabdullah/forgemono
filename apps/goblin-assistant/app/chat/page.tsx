"use client";

import React, { useState, useRef, useEffect } from 'react';
import { ArrowUp, User, Loader, Star, MessageSquare } from 'lucide-react';
import { Button } from '@/components/ui';
import { Badge } from '@/components/ui/Badge';
import { Input } from '@/components/ui/input';

interface Message {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  status?: 'sending' | 'sent' | 'error';
}

interface ChatSession {
  id: string;
  title: string;
  messages: Message[];
  createdAt: Date;
}

interface SendMessageResponse {
  message_id: string;
  response: string;
  provider: string;
  model: string;
  timestamp: string;
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [currentSession, setCurrentSession] = useState<ChatSession | null>(null);
  const [showScrollButton, setShowScrollButton] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const shouldAutoScroll = useRef(true);

  // Persistent user ID stored in localStorage
  const [userId] = useState<string>(() => {
    if (typeof window !== 'undefined') {
      const stored = localStorage.getItem('goblin_user_id');
      if (stored) return stored;
    }
    const newId = 'user-' + crypto.randomUUID();
    if (typeof window !== 'undefined') {
      localStorage.setItem('goblin_user_id', newId);
    }
    return newId;
  });

  // Load messages from localStorage on mount
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const storedMessages = localStorage.getItem('goblin_chat_messages');
      if (storedMessages) {
        try {
          const parsedMessages = JSON.parse(storedMessages).map((msg: any) => ({
            ...msg,
            timestamp: new Date(msg.timestamp)
          }));
          setMessages(parsedMessages);

          const newSession: ChatSession = {
            id: 'session-' + Date.now(),
            title: 'Restored Conversation',
            messages: parsedMessages,
            createdAt: new Date()
          };
          setCurrentSession(newSession);
        } catch (error) {
          console.error('Failed to load stored messages:', error);
          // Fall back to welcome message
          initializeWelcomeMessage();
        }
      } else {
        initializeWelcomeMessage();
      }
    }
  }, []);

  // Save messages to localStorage whenever they change
  useEffect(() => {
    if (messages.length > 0 && typeof window !== 'undefined') {
      localStorage.setItem('goblin_chat_messages', JSON.stringify(messages));
    }
  }, [messages]);

  // Smart auto-scroll: only scroll if user is near bottom and hasn't scrolled up
  useEffect(() => {
    const container = messagesContainerRef.current;
    if (container && shouldAutoScroll.current) {
      const { scrollTop, scrollHeight, clientHeight } = container;
      const isAtBottom = scrollTop + clientHeight >= scrollHeight - 50; // 50px threshold
      if (isAtBottom) {
        // Add a small delay to prevent jarring auto-scroll
        setTimeout(() => {
          messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
        }, 100);
      }
    }
  }, [messages]);

  // Track scroll position to determine if we should auto-scroll
  const handleScroll = () => {
    if (messagesContainerRef.current) {
      const { scrollTop, scrollHeight, clientHeight } = messagesContainerRef.current;
      const isNearBottom = scrollTop + clientHeight >= scrollHeight - 100; // 100px threshold
      const isScrolledUp = scrollTop < scrollHeight - clientHeight - 200; // Show button if scrolled up more than 200px

      shouldAutoScroll.current = isNearBottom;
      setShowScrollButton(isScrolledUp);
    }
  };

  // Scroll to bottom function
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    setShowScrollButton(false);
  };

  const initializeWelcomeMessage = () => {
    const welcomeMessage: Message = {
      id: 'welcome',
      type: 'assistant',
      content: "Hello! I'm your AI assistant. How can I help you today?",
      timestamp: new Date(),
      status: 'sent'
    };

    const newSession: ChatSession = {
      id: 'session-' + Date.now(),
      title: 'New Conversation',
      messages: [welcomeMessage],
      createdAt: new Date()
    };

    setMessages([welcomeMessage]);
    setCurrentSession(newSession);
  };

  const handleSendMessage = async (content: string) => {
    if (!content.trim() || isTyping) return;

    // Input validation: Check message length (max 1000 characters)
    if (content.trim().length > 1000) {
      const errorMessage: Message = {
        id: 'error-' + Date.now(),
        type: 'assistant',
        content: 'Message is too long. Please keep it under 1000 characters.',
        timestamp: new Date(),
        status: 'error'
      };
      setMessages(prev => [...prev, errorMessage]);
      return;
    }

    const userMessage: Message = {
      id: 'user-' + Date.now(),
      type: 'user',
      content: content.trim(),
      timestamp: new Date(),
      status: 'sending'
    };

    // Add user message to messages
    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsTyping(true);

    try {
      // Use the correct API base URL from environment variables
      const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8004';

      // Get conversation history for context
      const conversationMessages = messages
        .filter(msg => msg.status !== 'error') // Exclude error messages from context
        .map(msg => ({
          role: msg.type,
          content: msg.content
        }));

      // Add the new user message to the conversation
      conversationMessages.push({
        role: 'user',
        content: content.trim()
      });

      // Send message using Goblin Assistant API
      const sendResponse = await fetch(`${apiBaseUrl}/api/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          messages: conversationMessages,
          provider: 'ollama_gcp', // Use GCP Ollama provider
          model: 'qwen2.5:3b'
        })
      });

      // Check response status and parse error body if needed
      if (!sendResponse.ok) {
        let errorMessage = 'Failed to send message';
        try {
          const errorData = await sendResponse.json();
          if (errorData.error?.message) {
            errorMessage = errorData.error.message;
          } else if (errorData.detail) {
            errorMessage = errorData.detail;
          }
        } catch (e) {
          // If we can't parse error body, use status text
          errorMessage = `Failed to send message: ${sendResponse.status} ${sendResponse.statusText}`;
        }
        throw new Error(errorMessage);
      }

      const responseData = await sendResponse.json();

      // Validate Goblin Assistant API response structure
      if (!responseData || typeof responseData !== 'object') {
        throw new Error('Invalid response format: expected object');
      }

      // Check if the request was successful
      if (!responseData.ok) {
        const errorMsg = responseData.error || 'Unknown error occurred';
        throw new Error(`API Error: ${errorMsg}`);
      }

      // Extract the response text
      const assistantContent = responseData.result?.text || responseData.result?.response || '';
      
      if (!assistantContent || typeof assistantContent !== 'string') {
        throw new Error('Invalid response format: missing or invalid response content');
      }

      // Create assistant message from validated response
      const assistantMessage: Message = {
        id: 'assistant-' + Date.now(),
        type: 'assistant',
        content: assistantContent.trim(),
        timestamp: new Date(),
        status: 'sent'
      };

      setMessages(prev => [...prev, assistantMessage]);

      // Update current session with new messages
      setCurrentSession(prev => {
        if (!prev) return prev;
        return {
          ...prev,
          messages: [...prev.messages, userMessage, assistantMessage]
        };
      });

    } catch (error) {
      console.error('Error sending message:', error);

      // Map technical errors to user-friendly messages
      let userFriendlyMessage = 'I apologize, but I encountered an error. Please try again.';

      if (error instanceof Error) {
        const errorMsg = error.message.toLowerCase();

        if (errorMsg.includes('401') || errorMsg.includes('unauthorized') || errorMsg.includes('api key') || errorMsg.includes('invalid public api key')) {
          userFriendlyMessage = 'Authentication failed. Please check your API key configuration.';
        } else if (errorMsg.includes('403') || errorMsg.includes('forbidden')) {
          userFriendlyMessage = 'Access denied. Please check your permissions.';
        } else if (errorMsg.includes('429') || errorMsg.includes('rate limit')) {
          userFriendlyMessage = 'Too many requests. Please wait a moment and try again.';
        } else if (errorMsg.includes('500') || errorMsg.includes('internal server error')) {
          userFriendlyMessage = 'Server error occurred. Please try again in a few moments.';
        } else if (errorMsg.includes('network') || errorMsg.includes('connection')) {
          userFriendlyMessage = 'Connection error. Please check your internet connection and try again.';
        } else if (errorMsg.includes('timeout')) {
          userFriendlyMessage = 'Request timed out. Please try again.';
        }
      }

      // Provide user-friendly error response
      const errorMessage: Message = {
        id: 'error-' + Date.now(),
        type: 'assistant',
        content: userFriendlyMessage,
        timestamp: new Date(),
        status: 'error'
      };

      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsTyping(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage(inputValue);
    }
  };

  const handleVoiceInput = () => {
    // TODO: Implement Web Speech API for voice input
    alert('Voice input feature coming soon!');
  };

  const clearChat = () => {
    const welcomeMessage: Message = {
      id: 'welcome',
      type: 'assistant',
      content: "Hello! I'm your AI assistant. How can I help you today?",
      timestamp: new Date(),
      status: 'sent'
    };

    setMessages([welcomeMessage]);
    setCurrentSession({
      ...currentSession!,
      messages: [welcomeMessage],
      title: 'New Conversation'
    });
  };

  const regenerateResponse = async () => {
    const lastAssistantMessageIndex = messages.map((msg, index) => ({ msg, index }))
      .filter(({ msg }) => msg.type === 'assistant')
      .pop()?.index;

    if (lastAssistantMessageIndex !== undefined) {
      // Find the user message that prompted this response
      const userMessages = messages.slice(0, lastAssistantMessageIndex)
        .filter(msg => msg.type === 'user');

      if (userMessages.length > 0) {
        const lastUserMessage = userMessages[userMessages.length - 1];

        // Remove the last assistant message
        setMessages(prev => prev.slice(0, lastAssistantMessageIndex));
        setIsTyping(true);

        try {
          // Use the correct API base URL and key from environment variables
          const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8003';
          const apiKey = process.env.NEXT_PUBLIC_API_KEY;

          if (!apiKey) {
            throw new Error('API key not configured. Please set NEXT_PUBLIC_API_KEY in your environment.');
          }

          // Get conversation history up to the last user message for context
          const conversationMessages = messages
            .slice(0, lastAssistantMessageIndex)
            .filter(msg => msg.status !== 'error') // Exclude error messages from context
            .map(msg => ({
              role: msg.type,
              content: msg.content
            }));

          // Send message using OpenAI-compatible API
          const sendResponse = await fetch(`${apiBaseUrl}/chat/completions`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'x-api-key': apiKey
            },
            body: JSON.stringify({
              model: 'goblin-simple:latest',
              messages: conversationMessages,
              max_tokens: 500,
              temperature: 0.9 // Higher temperature for more varied responses
            })
          });

          // Check response status and parse error body if needed
          if (!sendResponse.ok) {
            let errorMessage = 'Failed to regenerate response';
            try {
              const errorData = await sendResponse.json();
              if (errorData.error?.message) {
                errorMessage = errorData.error.message;
              } else if (errorData.detail) {
                errorMessage = errorData.detail;
              }
            } catch (e) {
              errorMessage = `Failed to regenerate: ${sendResponse.status} ${sendResponse.statusText}`;
            }
            throw new Error(errorMessage);
          }

          const responseData = await sendResponse.json();

          // Validate response structure
          if (!responseData.choices || !Array.isArray(responseData.choices) || responseData.choices.length === 0) {
            throw new Error('Invalid response format for regeneration');
          }

          const choice = responseData.choices[0];
          if (!choice.message || !choice.message.content || typeof choice.message.content !== 'string') {
            throw new Error('Invalid response content for regeneration');
          }

          // Create new assistant message
          const newAssistantMessage: Message = {
            id: 'regenerated-' + Date.now(),
            type: 'assistant',
            content: choice.message.content.trim(),
            timestamp: new Date(),
            status: 'sent'
          };

          setMessages(prev => [...prev, newAssistantMessage]);

        } catch (error) {
          console.error('Error regenerating response:', error);

          let userFriendlyMessage = 'Failed to regenerate response. Please try again.';

          if (error instanceof Error) {
            const errorMsg = error.message.toLowerCase();
            if (errorMsg.includes('401') || errorMsg.includes('api key')) {
              userFriendlyMessage = 'Authentication failed during regeneration.';
            } else if (errorMsg.includes('429')) {
              userFriendlyMessage = 'Too many requests. Please wait before regenerating.';
            }
          }

          const errorMessage: Message = {
            id: 'regenerate-error-' + Date.now(),
            type: 'assistant',
            content: userFriendlyMessage,
            timestamp: new Date(),
            status: 'error'
          };

          setMessages(prev => [...prev, errorMessage]);
        } finally {
          setIsTyping(false);
        }
      }
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      {/* Animated Background */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-0 left-0 w-full h-full">
          <div className="absolute top-20 left-10 w-72 h-72 bg-emerald-500/5 rounded-full blur-3xl animate-pulse"></div>
          <div className="absolute top-40 right-10 w-96 h-96 bg-purple-500/5 rounded-full blur-3xl animate-pulse delay-1000"></div>
          <div className="absolute bottom-20 left-1/3 w-80 h-80 bg-blue-500/5 rounded-full blur-3xl animate-pulse delay-500"></div>
        </div>
      </div>

      {/* Main Content */}
      <div className="relative z-10">
        {/* Header */}
        <header className="border-b border-white/20 bg-gradient-to-r from-white/10 to-white/5 backdrop-blur-sm">
          <div className="container mx-auto px-6 py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <div className="w-10 h-10 bg-gradient-to-r from-emerald-500 to-blue-500 rounded-xl flex items-center justify-center shadow-lg shadow-emerald-500/20">
                  <Star className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h1 className="text-xl font-bold text-white">AI Chat Assistant</h1>
                  <p className="text-slate-400 text-sm">Intelligent conversations powered by multi-model routing</p>
                </div>
              </div>
              
              <div className="flex items-center space-x-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={clearChat}
                  className="border-white/30 text-white hover:bg-white/10 font-semibold px-3 py-1.5 rounded-lg transition-all duration-300 backdrop-blur-sm"
                >
                  New Chat
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={regenerateResponse}
                  disabled={isTyping || messages.length === 0}
                  className="border-white/30 text-white hover:bg-white/10 font-semibold px-3 py-1.5 rounded-lg transition-all duration-300 backdrop-blur-sm"
                >
                  Regenerate
                </Button>
              </div>
            </div>
          </div>
        </header>

        {/* Chat Messages */}
        <main className="container mx-auto px-6 py-6 max-w-4xl relative">
          <div
            ref={messagesContainerRef}
            onScroll={handleScroll}
            className="bg-gradient-to-br from-white/10 to-white/5 backdrop-blur-sm border border-white/20 rounded-2xl p-6 shadow-xl max-h-[60vh] overflow-y-auto"
          >
            <div className="space-y-6">
              {messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div className={`flex items-start space-x-3 max-w-xs lg:max-w-md ${
                    message.type === 'user' ? 'flex-row-reverse space-x-reverse' : ''
                  }`}>
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                      message.type === 'user'
                        ? 'bg-gradient-to-r from-emerald-500 to-blue-500'
                        : 'bg-gradient-to-r from-purple-500 to-pink-500'
                    }`}>
                      {message.type === 'user' ? (
                        <User className="w-4 h-4 text-white" />
                      ) : (
                        <MessageSquare className="w-4 h-4 text-white" />
                      )}
                    </div>

                    <div className={`px-4 py-3 rounded-2xl ${
                      message.type === 'user'
                        ? 'bg-gradient-to-r from-emerald-500/20 to-blue-500/20 text-white border border-white/20'
                        : 'bg-gradient-to-r from-purple-500/20 to-pink-500/20 text-white border border-white/20'
                    }`}>
                      <p className="text-sm leading-relaxed">{message.content}</p>
                      <div className="flex items-center justify-between mt-2">
                        <span className="text-xs text-slate-300">
                          {message.timestamp.toLocaleTimeString()}
                        </span>
                        {message.status === 'sending' && (
                          <Loader className="w-3 h-3 text-slate-300 animate-spin" />
                        )}
                        {message.status === 'error' && (
                          <span className="text-xs text-red-400">Failed to send</span>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              ))}

              {/* Typing Indicator */}
              {isTyping && (
                <div className="flex justify-start">
                  <div className="flex items-start space-x-3">
                    <div className="w-8 h-8 rounded-full bg-gradient-to-r from-purple-500 to-pink-500 flex items-center justify-center">
                      <MessageSquare className="w-4 h-4 text-white" />
                    </div>
                    <div className="bg-gradient-to-r from-purple-500/20 to-pink-500/20 border border-white/20 rounded-2xl px-4 py-3">
                      <div className="flex space-x-2">
                        <div className="w-2 h-2 bg-purple-400 rounded-full animate-bounce"></div>
                        <div className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                        <div className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>
          </div>

          {/* Scroll to Bottom Button */}
          {showScrollButton && (
            <Button
              onClick={scrollToBottom}
              className="absolute bottom-4 right-4 bg-gradient-to-r from-emerald-500 to-blue-500 hover:from-emerald-600 hover:to-blue-600 text-white rounded-full p-3 shadow-lg hover:shadow-xl transition-all duration-300"
              size="icon"
            >
              <ArrowUp className="w-5 h-5" />
            </Button>
          )}
        </main>

        {/* Input Area */}
        <footer className="container mx-auto px-6 pb-8">
          <div className="bg-gradient-to-r from-white/10 to-white/5 backdrop-blur-sm border border-white/20 rounded-2xl p-4 shadow-xl">
            <div className="flex items-end space-x-4">
              {/* Input Field */}
              <div className="flex-1 relative">
                <Input
                  ref={inputRef}
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Type your message here..."
                  disabled={isTyping}
                  className="w-full bg-white/10 border-white/20 text-white placeholder-slate-400 focus:border-white/40 focus:ring-0 focus:outline-none pr-16"
                />
                <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
                  <Badge variant="outline" className="bg-white/10 border-white/20 text-slate-300 text-xs">
                    Press Enter to send
                  </Badge>
                </div>
              </div>

              {/* Send Button */}
              <Button
                onClick={() => handleSendMessage(inputValue)}
                disabled={!inputValue.trim() || isTyping}
                className="bg-gradient-to-r from-emerald-500 to-blue-500 hover:from-emerald-600 hover:to-blue-600 text-white font-semibold px-6 py-2 rounded-xl transition-all duration-300 hover:shadow-xl hover:shadow-emerald-500/25 transform hover:-translate-y-1 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
              >
                <ArrowUp className="w-5 h-5" />
              </Button>
            </div>

            {/* Quick Actions */}
            <div className="flex items-center justify-between mt-4 pt-4 border-t border-white/20">
              <div className="flex items-center space-x-2 text-slate-400 text-sm">
                <Badge variant="outline" className="bg-white/10 border-white/20 text-slate-300">
                  Multi-model routing
                </Badge>
                <Badge variant="outline" className="bg-white/10 border-white/20 text-slate-300">
                  Privacy first
                </Badge>
                <Badge variant="outline" className="bg-white/10 border-white/20 text-slate-300">
                  Real-time responses
                </Badge>
              </div>

              <div className="flex items-center space-x-4 text-xs text-slate-400">
                <span className={`${inputValue.length > 900 ? 'text-yellow-400' : inputValue.length > 950 ? 'text-red-400' : ''}`}>
                  {inputValue.length}/1000
                </span>
                <span>{messages.length} messages • Ready to chat</span>
              </div>
            </div>
          </div>
        </footer>
      </div>
    </div>
  );
}
