import { useState, useEffect } from 'react';
import { apiClient } from '../api/client-axios';

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
 * Custom hook for managing dashboard data fetching and state
 * @returns Dashboard data, loading state, error state, and refresh function
 */
export function useDashboardData() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [dashboard, setDashboard] = useState<DashboardState | null>(null);

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

  return {
    dashboard,
    loading,
    error,
    refresh: loadDashboardData,
  };
}
