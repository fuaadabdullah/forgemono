import Link from 'next/link';

interface ChatHeaderProps {
  /** Show admin-only shortcuts when true. */
  isAdmin: boolean;
  /** Handler for clearing the current chat. */
  onClear: () => void;
}

const ChatHeader = ({ isAdmin, onClear }: ChatHeaderProps) => (
  <header className="border-b border-border bg-surface/80 backdrop-blur px-6 py-4">
    <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
      <div>
        <h1 className="text-2xl font-semibold text-text">Ask Anything</h1>
        <p className="text-sm text-muted">
          Drop in docs, notes, or questions. Get decisions, summaries, and next steps.
        </p>
      </div>
      <div className="flex flex-wrap gap-2">
        <button
          onClick={onClear}
          className="px-3 py-2 rounded-lg border border-border text-text hover:bg-surface-hover"
          type="button"
        >
          Clear Chat
        </button>
        <Link
          href="/search"
          className="px-3 py-2 rounded-lg bg-primary/15 text-primary hover:bg-primary/25"
        >
          Global Search
        </Link>
        {isAdmin && (
          <Link
            href="/admin"
            className="px-3 py-2 rounded-lg bg-surface-hover text-text hover:bg-surface-active"
          >
            Admin Dashboard
          </Link>
        )}
      </div>
    </div>
  </header>
);

export default ChatHeader;
