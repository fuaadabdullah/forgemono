import Link from 'next/link';
import Navigation from '../../components/Navigation';
import { useAuthStore } from '../../store/authStore';
import { BRAND_NAME, BRAND_TAGLINE, HOME_EXAMPLE_CARDS } from '../../content/brand';

const CustomerHome = ({ isAuthenticated }: { isAuthenticated: boolean }) => (
  <div className="min-h-screen bg-bg">
    <Navigation showLogout={isAuthenticated} variant="customer" />
    <div className="max-w-5xl mx-auto p-6">
      <main role="main" id="main-content" tabIndex={-1}>
        <section className="bg-surface border border-border rounded-2xl p-8 mb-8">
          <h1 className="text-3xl font-semibold text-text mb-2">{BRAND_NAME}</h1>
          <p className="text-muted mb-6">
            {BRAND_TAGLINE} Drop in docs, notes, and logs. Get answers, summaries, and next steps.
          </p>
          <div className="flex flex-wrap gap-3">
            <Link
              href="/chat"
              className="px-4 py-2 rounded-lg bg-primary text-text-inverse font-medium shadow-glow-primary hover:brightness-110"
            >
              Open Chat
            </Link>
            <Link
              href="/search"
              className="px-4 py-2 rounded-lg bg-primary/15 text-text border border-border hover:bg-primary/20 font-medium"
            >
              Search Memory
            </Link>
            <Link
              href="/help"
              className="px-4 py-2 rounded-lg bg-surface-hover text-text border border-border hover:bg-surface-active font-medium"
            >
              Get Help
            </Link>
          </div>
        </section>

        <div className="grid gap-4 lg:grid-cols-[1.2fr_1fr]">
          <section className="bg-surface border border-border rounded-2xl p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-text">Recent Conversation</h2>
              <Link href="/chat" className="text-sm text-primary hover:underline">
                View all
              </Link>
            </div>
            <div className="rounded-xl border border-dashed border-border p-4 text-sm text-muted">
              No recent conversations yet. Start a chat and it will show up here.
            </div>
          </section>

          <section className="bg-surface border border-border rounded-2xl p-6">
            <h2 className="text-lg font-semibold text-text mb-4">Quick Actions</h2>
            <div className="grid gap-3">
              <Link
                href="/chat"
                className="flex items-center justify-between rounded-xl border border-border bg-surface-hover px-4 py-3 hover:bg-surface-active"
              >
                <span className="text-sm font-medium text-text">Summon an answer</span>
                <span className="text-lg">💬</span>
              </Link>
              <Link
                href="/search"
                className="flex items-center justify-between rounded-xl border border-border bg-surface-hover px-4 py-3 hover:bg-surface-active"
              >
                <span className="text-sm font-medium text-text">Search your knowledge</span>
                <span className="text-lg">🔍</span>
              </Link>
              <Link
                href="/sandbox"
                className="flex items-center justify-between rounded-xl border border-border bg-surface-hover px-4 py-3 hover:bg-surface-active"
              >
                <span className="text-sm font-medium text-text">Run a safe experiment</span>
                <span className="text-lg">🧪</span>
              </Link>
            </div>
          </section>
        </div>

        <section className="mt-6 grid gap-4 md:grid-cols-3">
          {HOME_EXAMPLE_CARDS.map(item => (
            <div
              key={item.title}
              className="bg-surface border border-border rounded-2xl p-5 hover:bg-surface-hover transition-colors"
            >
              <div className="text-2xl mb-2">{item.icon}</div>
              <h3 className="text-base font-semibold text-text mb-2">{item.title}</h3>
              <p className="text-sm text-muted">{item.body}</p>
            </div>
          ))}
        </section>
      </main>
    </div>
  </div>
);

export default function HomeScreen() {
  const isAuthenticated = useAuthStore(state => state.isAuthenticated);
  return <CustomerHome isAuthenticated={isAuthenticated} />;
}
