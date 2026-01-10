import { useState, useEffect } from 'react';
import { runtimeClient } from '../api/api-client';
import { CostEstimate, computeLocalCostEstimate, tokensFromChars } from '../utils/costUtils';

interface UseCostEstimationProps {
  orchestrationText: string;
  codeInput?: string;
  provider?: string;
  model?: string;
  onEstimatedCostChange?: (cost: number) => void;
}

export const useCostEstimation = ({
  orchestrationText,
  codeInput = '',
  provider,
  model,
  onEstimatedCostChange,
}: UseCostEstimationProps) => {
  const [estimate, setEstimate] = useState<CostEstimate | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [rateLimitInfo, setRateLimitInfo] = useState<CostEstimate['rateLimit'] | null>(null);

  useEffect(() => {
    if (orchestrationText.trim()) {
      calculateEstimate();
    } else {
      setEstimate(null);
      onEstimatedCostChange?.(0);
      setRateLimitInfo(null);
      setError(null);
    }
  }, [orchestrationText, codeInput, provider, model]);

  const calculateEstimate = async () => {
    if (!orchestrationText.trim()) return;

    setLoading(true);
    setError(null);

    try {
      const backendEstimate = await (runtimeClient as any).estimateCost(
        orchestrationText,
        codeInput,
        provider,
        model
      );

      const costEstimate: CostEstimate = {
        totalCost: backendEstimate.totalCost,
        stepCosts: backendEstimate.stepCosts,
        currency: backendEstimate.currency,
        rateLimit: backendEstimate.rateLimit,
      };

      setEstimate(costEstimate);
      setRateLimitInfo(backendEstimate.rateLimit ?? null);
      onEstimatedCostChange?.(backendEstimate.totalCost);
    } catch (err: any) {
      // Log error via runtime client if available; otherwise set error for user
      if ((runtimeClient as any)?.log?.error) {
        (runtimeClient as any).log.error('Cost estimation error', err);
      }

      const message =
        (err && ((err.message as string) || (err.toString && err.toString()))) || 'API unavailable';
      if (/credential|auth|api key/i.test(message)) {
        setError('Pricing API credentials missing — using local cached rates');
      } else if (/429|rate limit|too many requests/i.test(message)) {
        const retry = err?.retryAfter ? ` Retry after ${err.retryAfter}s.` : '';
        setError(`Pricing API rate limit reached — using local cached rates.${retry}`);
      } else {
        setError('Using local estimate (API unavailable)');
      }

      // Fallback: compute local conservative estimate using cached rates
      const localEstimate = computeLocalCostEstimate(orchestrationText, codeInput, provider, model);
      const costEstimate: CostEstimate = {
        totalCost: localEstimate,
        stepCosts: [
          {
            stepId: 'local-1',
            goblin: 'Local Est',
            task: 'Local estimate',
            estimatedCost: localEstimate,
            tokenEstimate: tokensFromChars(orchestrationText.length + codeInput.length),
          },
        ],
        currency: 'USD',
      };

      setEstimate(costEstimate);
      onEstimatedCostChange?.(localEstimate);
    } finally {
      setLoading(false);
    }
  };

  return {
    estimate,
    loading,
    error,
    rateLimitInfo,
    calculateEstimate,
  };
};
