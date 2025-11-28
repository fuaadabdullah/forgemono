import { useState, useEffect } from 'react';
import { apiClient } from '../api/client';

interface Goblin {
  id: string;
  name: string;
  title: string;
  status: string;
  guild: string;
}

interface HealthStatus {
  status: string;
  timestamp: number;
  version: string;
  services: {
    routing: string;
    execution: string;
    search: string;
    auth: string;
  };
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
        setHealth(healthData);
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
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-900 border border-red-700 rounded-lg p-4">
        <h3 className="text-red-400 font-semibold">Error</h3>
        <p className="text-red-300">{error}</p>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div className="text-center">
        <h1 className="text-4xl font-bold text-white mb-4">GoblinOS Assistant Dashboard</h1>
        <p className="text-gray-400 text-lg">
          AI-powered development assistant with intelligent model routing
        </p>
      </div>

      {/* Health Status */}
      {health && (
        <div className="bg-gray-800 rounded-lg p-6">
          <h2 className="text-2xl font-semibold text-white mb-4">System Health</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className={`text-2xl mb-2 ${health.status === 'healthy' ? 'text-green-400' : 'text-red-400'}`}>
                {health.status === 'healthy' ? '✅' : '❌'}
              </div>
              <div className="text-sm text-gray-400">Overall Status</div>
            </div>
            <div className="text-center">
              <div className={`text-2xl mb-2 ${health.services.routing === 'healthy' ? 'text-green-400' : 'text-red-400'}`}>
                {health.services.routing === 'healthy' ? '🚀' : '❌'}
              </div>
              <div className="text-sm text-gray-400">Routing</div>
            </div>
            <div className="text-center">
              <div className={`text-2xl mb-2 ${health.services.execution === 'healthy' ? 'text-green-400' : 'text-red-400'}`}>
                {health.services.execution === 'healthy' ? '⚡' : '❌'}
              </div>
              <div className="text-sm text-gray-400">Execution</div>
            </div>
            <div className="text-center">
              <div className={`text-2xl mb-2 ${health.services.auth === 'healthy' ? 'text-green-400' : 'text-red-400'}`}>
                {health.services.auth === 'healthy' ? '🔐' : '❌'}
              </div>
              <div className="text-sm text-gray-400">Auth</div>
            </div>
          </div>
        </div>
      )}

      {/* Available Goblins */}
      <div className="bg-gray-800 rounded-lg p-6">
        <h2 className="text-2xl font-semibold text-white mb-4">Available Goblins</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {goblins.map((goblin) => (
            <div key={goblin.id} className="bg-gray-700 rounded-lg p-4 hover:bg-gray-600 transition-colors">
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-lg font-semibold text-white">{goblin.title}</h3>
                <span className={`px-2 py-1 rounded-full text-xs ${
                  goblin.status === 'available'
                    ? 'bg-green-900 text-green-300'
                    : 'bg-red-900 text-red-300'
                }`}>
                  {goblin.status}
                </span>
              </div>
              <p className="text-gray-400 text-sm mb-2">{goblin.name}</p>
              <div className="text-xs text-gray-500">Guild: {goblin.guild}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Quick Actions */}
      <div className="bg-gray-800 rounded-lg p-6">
        <h2 className="text-2xl font-semibold text-white mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <a
            href="/execute"
            className="bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-4 rounded-lg transition-colors text-center"
          >
            Execute Task
          </a>
          <a
            href="/orchestrate"
            className="bg-purple-600 hover:bg-purple-700 text-white font-semibold py-3 px-4 rounded-lg transition-colors text-center"
          >
            Create Orchestration
          </a>
          <a
            href="/search"
            className="bg-green-600 hover:bg-green-700 text-white font-semibold py-3 px-4 rounded-lg transition-colors text-center"
          >
            Search & Debug
          </a>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
