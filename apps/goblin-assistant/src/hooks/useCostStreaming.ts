import { useState } from 'react';
import { runtimeClient } from '../api/api-client';
import { formatSummaryText, CostEstimate } from '../utils/costUtils';

interface UseCostStreamingProps {
  estimate: CostEstimate | null;
}

export const useCostStreaming = ({ estimate }: UseCostStreamingProps) => {
  const [streamLines, setStreamLines] = useState<string[]>([]);
  const [streaming, setStreaming] = useState<boolean>(false);
  const [showSummary, setShowSummary] = useState<boolean>(false);

  const startStreaming = async (
    orchestrationText: string,
    codeInput: string,
    provider?: string,
    model?: string
  ) => {
    setStreaming(true);
    setStreamLines([]);
    setShowSummary(false);

    try {
      // Use streaming client if available
      if ((runtimeClient as any).estimateCostStream) {
        await (runtimeClient as any).estimateCostStream(
          orchestrationText,
          codeInput,
          provider,
          model,
          (chunk: string) => {
            setStreamLines((prev) => [...prev, chunk]);
          }
        );
      }
    } finally {
      setStreaming(false);
      setShowSummary(true);
      // Ensure the summary will be created from estimate
      if (!streamLines.length && estimate) {
        setStreamLines([formatSummaryText(estimate)]);
      }
    }
  };

  const resetStreaming = () => {
    setStreamLines([]);
    setStreaming(false);
    setShowSummary(false);
  };

  return {
    streamLines,
    streaming,
    showSummary,
    startStreaming,
    resetStreaming,
  };
};
