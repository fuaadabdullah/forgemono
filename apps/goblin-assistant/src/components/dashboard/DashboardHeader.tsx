import { Button } from '../ui';
import { RefreshCw, Settings } from 'lucide-react';

interface DashboardHeaderProps {
  onRefresh: () => void;
  autoRefresh: boolean;
  onToggleAutoRefresh: () => void;
  loading: boolean;
}

/**
 * Dashboard header with title, refresh controls, and settings
 */
export function DashboardHeader({
  onRefresh,
  autoRefresh,
  onToggleAutoRefresh,
  loading,
}: DashboardHeaderProps) {
  return (
    <div className="flex items-center justify-between mb-6">
      <div>
        <h1 className="text-3xl font-bold text-foreground">System Health Dashboard</h1>
        <p className="text-muted-foreground mt-1">
          Real-time monitoring of all Goblin Assistant services and infrastructure
        </p>
      </div>

      <div className="flex items-center gap-3">
        <Button
          variant={autoRefresh ? 'primary' : 'secondary'}
          size="sm"
          onClick={onToggleAutoRefresh}
          className="flex items-center gap-2"
        >
          <RefreshCw className={`h-4 w-4 ${autoRefresh ? 'animate-spin' : ''}`} />
          Auto Refresh
        </Button>

        <Button
          variant="secondary"
          size="sm"
          onClick={onRefresh}
          disabled={loading}
          className="flex items-center gap-2"
        >
          <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </Button>

        <Button variant="secondary" size="sm" className="flex items-center gap-2">
          <Settings className="h-4 w-4" />
          Settings
        </Button>
      </div>
    </div>
  );
}
