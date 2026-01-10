import { useState } from 'react';
import { formatSummaryText, CostEstimate } from '../utils/costUtils';

export const useCostClipboard = () => {
  const [copyStatus, setCopyStatus] = useState<string | null>(null);

  const copyFormattedSummary = async (estimate: CostEstimate | null) => {
    const text = formatSummaryText(estimate);
    if (!text) return;

    try {
      await navigator.clipboard.writeText(text);
      setCopyStatus('Copied');
      setTimeout(() => setCopyStatus(null), 1500);
    } catch (err) {
      setCopyStatus('Copy failed');
      setTimeout(() => setCopyStatus(null), 1500);
    }
  };

  return {
    copyStatus,
    copyFormattedSummary,
  };
};
