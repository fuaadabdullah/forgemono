import React from 'react';
import { Button, Badge } from '../ui';
import { CostEstimate, formatSummaryText } from '../../utils/costUtils';

interface CostSummaryProps {
  estimate: CostEstimate | null;
  showSummary: boolean;
  copyStatus: string | null;
  onCopy: () => void;
}

export const CostSummary: React.FC<CostSummaryProps> = ({
  estimate,
  showSummary,
  copyStatus,
  onCopy,
}) => {
  if (!showSummary || !estimate) return null;

  return (
    <div className="formatted-summary">
      <div className="summary-header">
        <h5>Formatted Summary</h5>
        <div className="summary-actions">
          <Button aria-label="Copy formatted docs" onClick={onCopy} size="sm">
            Copy formatted docs
          </Button>
          {copyStatus && <Badge className="copy-status">{copyStatus}</Badge>}
        </div>
      </div>
      <pre className="summary-pre">{formatSummaryText(estimate)}</pre>
    </div>
  );
};
