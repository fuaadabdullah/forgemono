import { useEffect, useState } from 'react';

export interface RateLimitInfo {
  remaining: number;
  limit: number;
  resetSeconds?: number;
}

export interface CostEstimate {
  estimatedCost: number;
  estimatedTokens: number;
  provider?: string;
  model?: string;
  breakdown?: Array<{ label: string; cost: number; tokens: number }>;
}

interface Options {
  orchestrationText: string;
  codeInput: string;
  provider?: string;
  model?: string;
  onEstimatedCostChange?: (cost: number) => void;
}

const computeEstimate = (orchestrationText: string, codeInput: string): CostEstimate => {
  const totalChars = orchestrationText.length + codeInput.length;
  const estimatedTokens = Math.max(8, Math.round(totalChars / 4));
  const estimatedCost = Number(((estimatedTokens / 1000) * 0.02).toFixed(4));

  return {
    estimatedCost,
    estimatedTokens,
    breakdown: [{ label: 'Estimated total', cost: estimatedCost, tokens: estimatedTokens }],
  };
};

export const useCostEstimation = ({
  orchestrationText,
  codeInput,
  provider,
  model,
  onEstimatedCostChange,
}: Options) => {
  const [estimate, setEstimate] = useState<CostEstimate | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [rateLimitInfo, setRateLimitInfo] = useState<RateLimitInfo | null>(null);

  useEffect(() => {
    if (!orchestrationText.trim()) {
      setEstimate(null);
      setError(null);
      return;
    }

    setLoading(true);
    setError(null);

    const nextEstimate = computeEstimate(orchestrationText, codeInput);
    nextEstimate.provider = provider;
    nextEstimate.model = model;

    setEstimate(nextEstimate);
    setRateLimitInfo({ remaining: 100, limit: 120, resetSeconds: 60 });
    onEstimatedCostChange?.(nextEstimate.estimatedCost);
    setLoading(false);
  }, [orchestrationText, codeInput, provider, model, onEstimatedCostChange]);

  return {
    estimate,
    loading,
    error,
    rateLimitInfo,
  };
};
