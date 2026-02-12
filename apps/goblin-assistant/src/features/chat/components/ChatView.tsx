import ChatHeader from './ChatHeader';
import ChatMessageList from './ChatMessageList';
import ChatComposer from './ChatComposer';
import ChatSidebar from './ChatSidebar';
import type { ChatSessionState } from '../hooks/useChatSession';

interface ChatViewProps {
  /** Chat session state + handlers. */
  session: ChatSessionState;
  /** Is the current user an admin. */
  isAdmin: boolean;
}

const ChatView = ({ session, isAdmin }: ChatViewProps) => {
  const {
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
  } = session;

  return (
    <div className="min-h-[calc(100vh-64px)] bg-bg">
      <div className="flex">
        <ChatSidebar
          threads={threads}
          isThreadsLoading={isThreadsLoading}
          activeThreadId={activeThreadId}
          onSelectThread={selectThread}
          onNewConversation={handleClearChat}
          isAdmin={isAdmin}
          totalTokens={totalTokens}
          messageCount={messages.length}
        />

        <main className="flex-1 flex flex-col bg-bg" aria-label="Chat">
          <ChatHeader isAdmin={isAdmin} onClear={handleClearChat} />
          <section className="flex-1 overflow-y-auto px-4 py-8">
            <ChatMessageList
              messages={messages}
              quickPrompts={quickPrompts}
              onPromptClick={handlePromptClick}
              bottomRef={bottomRef}
              isSending={isSending}
            />
          </section>
          <footer>
            <ChatComposer
              input={input}
              inputRef={inputRef}
              isSending={isSending}
              quickPrompts={quickPrompts}
              onInputChange={setInput}
              onClear={handleClearChat}
              onSend={() => sendMessage()}
              onKeyDown={handleKeyDown}
              onPromptClick={handlePromptClick}
            />
          </footer>
        </main>
      </div>
    </div>
  );
};

export default ChatView;
