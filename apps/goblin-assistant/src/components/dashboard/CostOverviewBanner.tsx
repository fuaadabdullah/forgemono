import Card from '../Card';
import { Badge } from '../ui';
import { DollarSign, TrendingUp, Calendar } from 'lucide-react';

interface CostOverviewBannerProps {
  totalCost: number;
  todayCost: number;
  thisMonthCost: number;
  byProvider: Record<string, number>;
}

/**
 * Cost overview banner component displaying total costs and breakdowns
 */
export function CostOverviewBanner({
  totalCost,
  todayCost,
  thisMonthCost,
  byProvider,
}: CostOverviewBannerProps) {
  const formatCurrency = (amount: number) => `$${amount.toFixed(4)}`;

  return (
    <Card className="mb-6">
      <div className="pb-3 mb-4 border-b border-border">
        <h3 className="flex items-center gap-2 text-lg font-semibold">
          <DollarSign className="h-5 w-5" />
          Cost Overview
        </h3>
      </div>

      <div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-100 rounded-lg">
              <DollarSign className="h-4 w-4 text-blue-600" />
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Total Cost</p>
              <p className="text-2xl font-bold">{formatCurrency(totalCost)}</p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="p-2 bg-green-100 rounded-lg">
              <TrendingUp className="h-4 w-4 text-green-600" />
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Today</p>
              <p className="text-2xl font-bold">{formatCurrency(todayCost)}</p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="p-2 bg-purple-100 rounded-lg">
              <Calendar className="h-4 w-4 text-purple-600" />
            </div>
            <div>
              <p className="text-sm text-muted-foreground">This Month</p>
              <p className="text-2xl font-bold">{formatCurrency(thisMonthCost)}</p>
            </div>
          </div>
        </div>

        <div className="flex flex-wrap gap-2">
          {Object.entries(byProvider).map(([provider, cost]) => (
            <Badge key={provider} variant="neutral" size="sm">
              {provider}: {formatCurrency(cost)}
            </Badge>
          ))}
        </div>
      </div>
    </Card>
  );
}
