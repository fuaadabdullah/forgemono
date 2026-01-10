import { useState, useEffect } from 'react';
import { DashboardSkeleton } from './LoadingSkeleton';
import { useDashboardData } from '../hooks/useDashboardData';
import { DashboardHeader } from './dashboard/DashboardHeader';
import { CostOverviewBanner } from './dashboard/CostOverviewBanner';
import { StatusCardsGrid } from './dashboard/StatusCardsGrid';
import { DashboardError } from './dashboard/DashboardError';
import { Grid } from './ui';
import StatusCard from './StatusCard';

/**
 * Global Health Dashboard
 * Comprehensive monitoring with expandable cards, sparklines, and error tracking
 * Refactored into smaller, focused components for better maintainability
 */
export default function EnhancedDashboard() {
  const [autoRefresh, setAutoRefresh] = useState(false);
  const { dashboard, loading, error, refresh } = useDashboardData();

  // Auto-refresh every 30 seconds if enabled
  useEffect(() => {
    if (!autoRefresh) return;
    const interval = setInterval(refresh, 30000);
    return () => clearInterval(interval);
  }, [autoRefresh, refresh]);

  if (loading) {
    return <DashboardSkeleton />;
  }

  if (error && !dashboard) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-bg p-4">
        <DashboardError error={error} onRetry={refresh} />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-bg py-6 px-4">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <DashboardHeader
          onRefresh={refresh}
          autoRefresh={autoRefresh}
          onToggleAutoRefresh={() => setAutoRefresh(!autoRefresh)}
          loading={loading}
        />

        {/* Live region for status updates */}
        <div className="sr-only" role="status" aria-live="polite" aria-atomic="true">
          {dashboard &&
            `Dashboard updated. Services: ${Object.values(dashboard).filter((s: any) => s.status === 'healthy').length} healthy`}
        </div>

        {/* Error banner (non-blocking) */}
        {error && dashboard && <DashboardError error={error} onRetry={refresh} />}

        {/* Cost Overview Banner */}
        {dashboard && (
          <CostOverviewBanner
            totalCost={dashboard.cost.total}
            todayCost={dashboard.cost.today}
            thisMonthCost={dashboard.cost.thisMonth}
            byProvider={dashboard.cost.byProvider}
          />
        )}

        {/* Health Cards Grid */}
        {dashboard && (
          <StatusCardsGrid
            backend={dashboard.backend}
            chroma={dashboard.chroma}
            mcp={dashboard.mcp}
            rag={dashboard.rag}
            sandbox={dashboard.sandbox}
          />
        )}

        {/* Quick Links Card */}
        <div className="bg-surface rounded-xl border border-border p-6">
          <h2 className="text-lg font-semibold text-text mb-4">Quick Links</h2>
          <Grid gap="sm">
            <a
              href="/providers"
              className="px-4 py-3 bg-primary text-text-inverse rounded-lg hover:brightness-110 shadow-glow-primary transition-all text-center font-medium block"
            >
              Manage Providers
            </a>
            <a
              href="/logs"
              className="px-4 py-3 bg-accent text-text-inverse rounded-lg hover:brightness-110 shadow-glow-accent transition-all text-center font-medium block"
            >
              View Logs
            </a>
            <a
              href="/sandbox"
              className="px-4 py-3 bg-success text-text-inverse rounded-lg hover:brightness-110 transition-all text-center font-medium block"
            >
              Sandbox Jobs
            </a>
            <a
              href="/settings"
              className="px-4 py-3 bg-surface-hover text-text border border-border rounded-lg hover:bg-surface-active transition-all text-center font-medium block"
            >
              Settings
            </a>
          </Grid>
        </div>
      </div>
    </div>
  );
}
