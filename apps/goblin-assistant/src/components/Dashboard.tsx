import { useState, useEffect } from 'react';
import { apiClient } from '../api/client-axios';
import { HealthStatus, isHealthStatus } from '../types/api';

interface Goblin {
  id: string;
  name: string;
  title: string;
  status: string;
  guild: string;
}

const Dashboard = () => {
  const [goblins, setGoblins] = useState<Goblin[]>([]);
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadDashboardData = async () => {
      try {
        setLoading(true);
        const [goblinsData, healthData] = await Promise.all([
          apiClient.getGoblins(),
          apiClient.getStreamingHealth(),
        ]);
        setGoblins(goblinsData);
        if (isHealthStatus(healthData)) {
          setHealth(healthData);
        } else {
          console.error('Invalid health status response');
          setHealth(null);
        }
      } catch (err) {
        setError('Failed to load dashboard data');
        console.error('Dashboard error:', err);
      } finally {
        setLoading(false);
      }
    };

    loadDashboardData();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-surface border-2 border-danger rounded-lg p-4">
        <h3 className="text-danger font-semibold">Error</h3>
        <p className="text-text">{error}</p>
      </div>
    );
  }

  return (
    <div className="space-y-10 max-w-7xl mx-auto px-4 py-6">
      <div className="text-center">
        <h1 className="text-4xl font-bold text-text mb-3">GoblinOS Assistant</h1>
        <p className="text-muted text-lg">AI-powered development assistant with intelligent model routing</p>
      </div>

      {/* Health Status */}
      {health && (
        <div className="bg-surface border border-border rounded-xl p-6 shadow-sm">
          <h2 className="text-xl font-semibold text-text mb-4">System Health</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className={`text-2xl mb-2 ${health.overall === 'healthy' ? 'text-success' : 'text-danger'}`}>
                {health.overall === 'healthy' ? '✅' : '❌'}
              </div>
              <div className="text-sm text-muted">Overall Status</div>
            </div>
            <div className="text-center">
              <div className={`text-2xl mb-2 ${health.services.routing?.status === 'healthy' ? 'text-success' : 'text-danger'}`}>
                {health.services.routing?.status === 'healthy' ? '🚀' : '❌'}
              </div>
              <div className="text-sm text-muted">Routing</div>
            </div>
            <div className="text-center">
              <div className={`text-2xl mb-2 ${health.services.execution?.status === 'healthy' ? 'text-success' : 'text-danger'}`}>
                {health.services.execution?.status === 'healthy' ? '⚡' : '❌'}
              </div>
              <div className="text-sm text-muted">Execution</div>
            </div>
            <div className="text-center">
              <div className={`text-2xl mb-2 ${health.services.auth?.status === 'healthy' ? 'text-success' : 'text-danger'}`}>
                {health.services.auth?.status === 'healthy' ? '🔐' : '❌'}
              </div>
              <div className="text-sm text-muted">Auth</div>
            </div>
          </div>
        </div>
      )}

      {/* Available Goblins */}
      <div className="bg-surface border border-border rounded-xl p-6 shadow-sm">
        <h2 className="text-xl font-semibold text-text mb-4">Available Goblins</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {goblins.map((goblin) => (
            <div key={goblin.id} className="bg-surface-hover rounded-lg p-4 hover:bg-surface-active transition-colors border border-border">
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-sm font-semibold text-text">{goblin.title}</h3>
                <span className={`px-2 py-1 rounded-full text-xs ${
                  goblin.status === 'available'
                    ? 'bg-success/20 text-success'
                    : 'bg-danger/20 text-danger'
                }`}>
                  {goblin.status}
                </span>
              </div>
              <p className="text-muted text-xs mb-2">{goblin.name}</p>
              <div className="text-xs text-muted">Guild: {goblin.guild}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Quick Actions */}
      <div className="bg-surface border border-border rounded-xl p-6 shadow-sm">
        <h2 className="text-xl font-semibold text-text mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <a
            href="/execute"
            className="bg-primary hover:brightness-110 text-text-inverse font-medium py-3 px-4 rounded-lg shadow-glow-primary transition-all text-center"
          >
            Execute Task
          </a>
          <a
            href="/orchestrate"
            className="bg-accent hover:brightness-110 text-text-inverse font-medium py-3 px-4 rounded-lg shadow-glow-accent transition-all text-center"
          >
            Create Orchestration
          </a>
          <a
            href="/search"
            className="bg-success hover:brightness-110 text-text-inverse font-medium py-3 px-4 rounded-lg transition-all text-center"
          >
            Search & Debug
          </a>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
