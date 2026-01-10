// Cost estimation utility functions
// Cached rate table in USD per token (conservative defaults). Exported for tests.
export const RATE_CACHE: Record<string, Record<string, number>> = {
  openai: {
    // example rates per token (not necessarily accurate, conservative defaults)
    'gpt-4': 0.03, // $0.03 per token (very conservative)
    'gpt-3.5': 0.000002,
    demo: 0.00002,
  },
  anthropic: {
    'claude-2': 0.00008,
    demo: 0.00003,
  },
  default: {
    demo: 0.00002,
  },
};

export const getCachedRate = (provider?: string, model?: string): number => {
  if (!provider) return RATE_CACHE.default.demo;
  const p = provider.toLowerCase();
  const providerRates = (RATE_CACHE as any)[p];
  if (!providerRates) return RATE_CACHE.default.demo;
  if (model && providerRates[model]) return providerRates[model];
  // fallback to 'demo' or the first rate
  return providerRates['demo'] || Object.values(providerRates)[0] || RATE_CACHE.default.demo;
};

export const tokensFromChars = (chars: number): number => Math.max(Math.ceil(chars / 4), 1);

export const computeLocalCostEstimate = (
  orchestration: string,
  code: string,
  provider?: string,
  model?: string
): number => {
  // Conservative local estimate: estimate tokens based on characters then multiply by cached rate
  const totalChars = (orchestration?.length || 0) + (code?.length || 0);
  const tokens = tokensFromChars(totalChars);
  const tokenRate = getCachedRate(provider, model);
  return Math.max(tokens * tokenRate, 0.001); // Minimum $0.001
};

export const formatCost = (cost: number): string => {
  if (cost < 0.001) {
    return `$${(cost * 1000).toFixed(2)}m`; // Millicents
  } else if (cost < 0.01) {
    return `$${cost.toFixed(4)}`; // Micro dollars
  } else {
    return `$${cost.toFixed(4)}`;
  }
};

export const getCostColor = (cost: number): string => {
  if (cost < 0.001) return 'cost-low'; // Very cheap
  if (cost < 0.01) return 'cost-medium'; // Reasonable
  if (cost < 0.1) return 'cost-high'; // Expensive
  return 'cost-very-high'; // Very expensive
};

export const formatSummaryText = (estimate: CostEstimate | null): string => {
  if (!estimate) return '';
  // Pretty JSON summary with key data only for readability
  const summary = {
    totalCost: estimate.totalCost,
    currency: estimate.currency,
    steps: estimate.stepCosts.map((s) => ({
      goblin: s.goblin,
      task: s.task,
      cost: s.estimatedCost,
      tokens: s.tokenEstimate,
    })),
  };
  return JSON.stringify(summary, null, 2);
};

export interface CostEstimate {
  totalCost: number;
  stepCosts: Array<{
    stepId: string;
    goblin: string;
    task: string;
    estimatedCost: number;
    tokenEstimate: number;
  }>;
  currency: string;
  rateLimit?: {
    limit: number;
    remaining: number;
    reset?: number;
  };
}
