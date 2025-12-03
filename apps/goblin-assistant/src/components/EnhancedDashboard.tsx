import { useState, useEffect } from 'react';
import { apiClient } from '../api/client-axios';
import StatusCard from './StatusCard';
import StatCard from './StatCard';
import { DashboardSkeleton } from './LoadingSkeleton';
import { Button, Alert, Grid } from './ui';

interface ServiceHealth {
  status: 'healthy' | 'degraded' | 'down' | 'unknown';
  lastCheck: string;
  latencyData: number[];
  errors: { timestamp: string; message: string }[];
  metrics: { label: string; value: string | number }[];
}

interface DashboardState {
  backend: ServiceHealth;
  chroma: ServiceHealth;
  mcp: ServiceHealth;
  rag: ServiceHealth;
  sandbox: ServiceHealth;
  cost: {
    total: number;
    today: number;
    thisMonth: number;
    byProvider: any;
  };
}

/**
 * Global Health Dashboard
 * Comprehensive monitoring with expandable cards, sparklines, and error tracking
 */
export default function EnhancedDashboard() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [dashboard, setDashboard] = useState<DashboardState | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(false);

  const loadDashboardData = async () => {
    try {
      setError(null);

      // Fetch consolidated dashboard data (single API call!)
      const [statusResult, costsResult] = await Promise.allSettled([
        apiClient.getDashboardStatus(),
        apiClient.getDashboardCosts(),
      ]);

      // Extract data or use fallbacks
      const status =
        statusResult.status === 'fulfilled'
          ? statusResult.value
          : {
              backend_api: { status: 'unknown', updated: new Date().toISOString() },
              vector_db: { status: 'unknown', updated: new Date().toISOString() },
              mcp_servers: { status: 'unknown', updated: new Date().toISOString() },
              rag_indexer: { status: 'unknown', updated: new Date().toISOString() },
              sandbox_runner: { status: 'unknown', updated: new Date().toISOString() },
              timestamp: new Date().toISOString(),
            };

      const costs =
        costsResult.status === 'fulfilled'
          ? costsResult.value
          : {
              total_cost: 0,
              cost_today: 0,
              cost_this_month: 0,
              by_provider: {},
              timestamp: new Date().toISOString(),
            };

      setDashboard({
        backend: {
          status: status.backend_api.status as any,
          lastCheck: status.backend_api.updated,
          latencyData: [], // Sparkline data can be fetched separately if needed
          errors: [],
          metrics: [
            {
              label: 'Latency',
              value: status.backend_api.latency_ms
                ? `${Math.round(status.backend_api.latency_ms)}ms`
                : 'N/A',
            },
            { label: 'Status', value: status.backend_api.status },
            {
              label: 'Error',
              value: status.backend_api.error || 'None',
            },
          ],
        },
        chroma: {
          status: status.vector_db.status as any,
          lastCheck: status.vector_db.updated,
          latencyData: [],
          errors: [],
          metrics: [
            {
              label: 'Collections',
              value: status.vector_db.details?.collections || 0,
            },
            {
              label: 'Documents',
              value: status.vector_db.details?.documents || 0,
            },
            {
              label: 'Latency',
              value: status.vector_db.latency_ms
                ? `${Math.round(status.vector_db.latency_ms)}ms`
                : 'N/A',
            },
          ],
        },
        mcp: {
          status: status.mcp_servers.status as any,
          lastCheck: status.mcp_servers.updated,
          latencyData: [],
          errors: [],
          metrics: [
            {
              label: 'Servers',
              value: status.mcp_servers.details?.count || 0,
            },
            {
              label: 'Active',
              value: status.mcp_servers.details?.servers?.length || 0,
            },
            { label: 'Status', value: status.mcp_servers.status },
          ],
        },
        rag: {
          status: status.rag_indexer.status as any,
          lastCheck: status.rag_indexer.updated,
          latencyData: [],
          errors: [],
          metrics: [
            {
              label: 'Running',
              value: status.rag_indexer.details?.running ? 'Yes' : 'No',
            },
            { label: 'Status', value: status.rag_indexer.status },
            { label: 'Error', value: status.rag_indexer.error || 'None' },
          ],
        },
        sandbox: {
          status: status.sandbox_runner.status as any,
          lastCheck: status.sandbox_runner.updated,
          latencyData: [],
          errors: [],
          metrics: [
            {
              label: 'Active Jobs',
              value: status.sandbox_runner.details?.active_jobs || 0,
            },
            {
              label: 'Queue Size',
              value: status.sandbox_runner.details?.queue_size || 0,
            },
            { label: 'Status', value: status.sandbox_runner.status },
          ],
        },
        cost: {
          total: costs.total_cost || 0,
          today: costs.cost_today || 0,
          thisMonth: costs.cost_this_month || 0,
          byProvider: costs.by_provider || {},
        },
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load dashboard');
      console.error('Dashboard error:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDashboardData();
  }, []);

  // Auto-refresh every 30 seconds if enabled
  useEffect(() => {
    if (!autoRefresh) return;
    const interval = setInterval(loadDashboardData, 30000);
    return () => clearInterval(interval);
  }, [autoRefresh]);

  // Retest function no longer used with StatusCards-only view

  if (loading) {
    return <DashboardSkeleton />;
  }

  if (error && !dashboard) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-bg p-4">
        <Alert
          variant="danger"
          title="Dashboard Error"
          message={
            <>
              <p className="mb-4">{error}</p>
              <div className="space-y-2">
                <Button
                  variant="danger"
                  fullWidth
                  icon="🔄"
                  onClick={() => {
                    setLoading(true);
                    setError(null);
                    loadDashboardData();
                  }}
                  aria-label="Retry loading dashboard"
                >
                  Retry
                </Button>
                <Button
                  variant="secondary"
                  fullWidth
                  onClick={() => window.location.reload()}
                >
                  Reload Page
                </Button>
              </div>
              <p className="text-xs text-muted mt-4 text-center">
                If this persists, check backend service status
              </p>
            </>
          }
          className="max-w-md"
        />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-bg py-6 px-4">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold text-text">
              🤖 Global Health Dashboard
            </h1>
            <p className="text-muted mt-1">
              Real-time monitoring of all backend services
            </p>
          </div>

          <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
            <Button
              variant="ghost"
              size="md"
              icon={<span className={loading ? 'animate-spin' : ''}>🔄</span>}
              onClick={loadDashboardData}
              disabled={loading}
              aria-label="Refresh dashboard data"
            >
              {loading ? 'Refreshing...' : 'Refresh'}
            </Button>
            <label className="flex items-center gap-2 px-4 py-2 bg-surface border border-border rounded-lg cursor-pointer hover:bg-surface-hover transition-colors">
              <input
                type="checkbox"
                checked={autoRefresh}
                onChange={(e) => setAutoRefresh(e.target.checked)}
                className="rounded border-border text-primary focus:ring-primary"
                aria-label="Enable auto-refresh every 30 seconds"
              />
              <span className="text-sm font-medium text-text whitespace-nowrap">
                Auto-refresh (30s)
              </span>
            </label>
          </div>
        </div>

        {/* Live region for status updates */}
        <div
          className="sr-only"
          role="status"
          aria-live="polite"
          aria-atomic="true"
        >
          {dashboard && `Dashboard updated. Services: ${Object.values(dashboard).filter((s: any) => s.status === 'healthy').length} healthy`}
        </div>

        {/* Error banner (non-blocking) */}
        {error && dashboard && (
          <Alert
            variant="warning"
            message={
              <>
                <p className="font-medium text-sm">{error}</p>
                <p className="text-xs mt-1">
                  Showing last successful data. Some information may be outdated.
                </p>
              </>
            }
            dismissible
            onDismiss={() => setError(null)}
          />
        )}

        {/* Cost Overview Banner */}
        {dashboard && (
          <div className="bg-surface rounded-xl p-4 border border-border">
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-base font-semibold text-text">Cost Tracking</h2>
              <p className="text-xs text-muted">Real-time API usage costs</p>
            </div>
            <Grid gap="md">
              <StatCard label="Today" value={`$${dashboard.cost.today.toFixed(2)}`} />
              <StatCard label="This Month" value={`$${dashboard.cost.thisMonth.toFixed(2)}`} />
              <StatCard label="All Time" value={`$${dashboard.cost.total.toFixed(2)}`} />
            </Grid>
          </div>
        )}

        {/* Health Cards Grid */}
        {dashboard && (
          <Grid gap="md" className="auto-rows-fr grid-flow-row-dense">
            <div className="h-full">
              <StatusCard
                title="Backend API"
                status={dashboard.backend.status}
                icon={"⚡"}
                meta={dashboard.backend.metrics}
                lastCheck={dashboard.backend.lastCheck}
                statusDetails={
                  dashboard.backend.status === 'degraded'
                    ? 'Backend API is responding but may have elevated latency or errors'
                    : undefined
                }
                className="h-full"
              />
            </div>

            <div className="h-full">
              <StatusCard
                title="Vector DB (Chroma)"
                status={dashboard.chroma.status}
                icon={"🗄️"}
                meta={dashboard.chroma.metrics}
                lastCheck={dashboard.chroma.lastCheck}
                statusDetails={
                  dashboard.chroma.status === 'down'
                    ? 'Vector database is not responding. RAG features unavailable.'
                    : dashboard.chroma.status === 'degraded'
                    ? 'Vector database responding slowly. Search performance may be reduced.'
                    : undefined
                }
                className="h-full"
              />
            </div>

            <div className="h-full">
              <StatusCard
                title="MCP Servers"
                status={dashboard.mcp.status}
                icon={"🔌"}
                meta={dashboard.mcp.metrics}
                lastCheck={dashboard.mcp.lastCheck}
                statusDetails={
                  dashboard.mcp.status === 'degraded'
                    ? 'Some MCP servers are not responding or have connection issues'
                    : undefined
                }
                className="h-full"
              />
            </div>

            <div className="h-full">
              <StatusCard
                title="RAG Indexer"
                status={dashboard.rag.status}
                icon={"🔍"}
                meta={dashboard.rag.metrics}
                lastCheck={dashboard.rag.lastCheck}
                statusDetails={
                  dashboard.rag.status === 'down'
                    ? 'RAG indexer process is not running. Document indexing unavailable.'
                    : undefined
                }
                className="h-full"
              />
            </div>

            <div className="h-full">
              <StatusCard
                title="Sandbox Runner"
                status={dashboard.sandbox.status}
                icon={"🐳"}
                meta={dashboard.sandbox.metrics}
                lastCheck={dashboard.sandbox.lastCheck}
                statusDetails={
                  dashboard.sandbox.status === 'degraded'
                    ? 'Sandbox has jobs queued or experiencing slower execution times'
                    : undefined
                }
                className="h-full"
              />
            </div>

            <div className="h-full">
              <StatusCard
                title="Quick Links"
                status="healthy"
                icon={"🚀"}
                meta={[
                  { label: 'Docs', value: 'Readme' },
                  { label: 'Providers', value: 'Configure' },
                  { label: 'Logs', value: 'View' },
                ]}
                className="h-full"
              />
            </div>
          </Grid>
        )}

        {/* Quick Actions */}
        <div className="bg-surface rounded-xl border border-border p-6">
          <h2 className="text-lg font-semibold text-text mb-4">
            Quick Actions
          </h2>
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
