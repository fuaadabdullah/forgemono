import { Alert } from '../ui';
import { AlertTriangle } from 'lucide-react';

interface DashboardErrorProps {
  error: string;
  onRetry: () => void;
}

/**
 * Error display component for dashboard failures
 */
export function DashboardError({ error, onRetry }: DashboardErrorProps) {
  return (
    <Alert
      variant="danger"
      title="Dashboard Error"
      message={
        <div>
          <p className="mb-3">{error}</p>
          <button
            onClick={onRetry}
            className="text-sm text-danger hover:text-danger/80 underline font-medium"
          >
            Try Again
          </button>
        </div>
      }
      icon={<AlertTriangle className="h-5 w-5" />}
      className="mb-6"
    />
  );
}
