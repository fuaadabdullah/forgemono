import React from 'react';
import { CostEstimate } from '../../utils/costUtils';

interface CostRateLimitProps {
  rateLimitInfo: CostEstimate['rateLimit'] | null;
}

export const CostRateLimit: React.FC<CostRateLimitProps> = ({ rateLimitInfo }) => {
  if (!rateLimitInfo) return null;

  return (
    <div className="rate-limit">
      API Rate Limit: {rateLimitInfo.remaining}/{rateLimitInfo.limit}
    </div>
  );
};
