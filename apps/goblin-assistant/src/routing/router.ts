// src/routing/router.ts
type Provider = {
  endpoint: string;
  api_key_env?: string | null;
  priority_tier?: number;
  capabilities?: string[];
  models?: string[];
  cost_score?: number;
  default_timeout_ms?: number;
  rate_limit_per_min?: number;
  invoke_path?: string;
};

type ProvidersMap = Record<string, Provider>;

type ProvidersConfig = {
  version: number;
  default_timeout_ms: number;
  providers: ProvidersMap;
};

import providersJson from '../../config/providers.json';

const config = providersJson as ProvidersConfig;
const PROVIDERS: ProvidersMap = config.providers;
const DEFAULT_TIMEOUT_MS = config.default_timeout_ms || 12000;

function movingAvg(arr: number[], n = 8): number | null {
  if (!arr || arr.length === 0) return null;
  const tail = arr.slice(-n);
  const sum = tail.reduce((s, currentValue) => s + currentValue, 0);
  return sum / tail.length;
}

// simple in-memory metrics mirror for UI (populated by backend telemetry if you push it)
const METRICS: Record<string, { latencies: number[]; succ: number; fail: number }> = {};

function ensureMetrics(pid: string) {
  if (!METRICS[pid]) METRICS[pid] = { latencies: [], succ: 0, fail: 0 };
}

export function updateMetricsFromBackend(pid: string, latencyMs: number, ok: boolean) {
  ensureMetrics(pid);
  METRICS[pid].latencies.push(latencyMs);
  if (METRICS[pid].latencies.length > 100) METRICS[pid].latencies.shift();
  if (ok) METRICS[pid].succ += 1;
  else METRICS[pid].fail += 1;
}

function scoreProvider(
  pid: string,
  capability: string,
  preferLocal = false,
  preferCost = false
): number {
  const p = PROVIDERS[pid] as Provider;
  if (!p.capabilities || p.capabilities.indexOf(capability) === -1) return Infinity;
  let score = 0;
  score += (p.priority_tier || 2) * 10;
  score += (p.cost_score || 0.5) * 5;
  const lat =
    movingAvg(METRICS[pid]?.latencies || []) ?? (p.default_timeout_ms || DEFAULT_TIMEOUT_MS) / 2;
  score += (lat / 1000) * 2;
  const succ = METRICS[pid]?.succ || 0;
  const fail = METRICS[pid]?.fail || 0;
  const total = succ + fail;
  const succRate = total > 0 ? succ / total : 0.9;
  score *= 1 - succRate * 0.45;
  if (preferLocal && (p.endpoint || '').startsWith('http://127.0.0.1')) score *= 0.6;
  if (preferCost) score += (p.cost_score || 0.5) * 10;
  score += Math.random() * 0.01;
  return score;
}

export function topProvidersFor(
  capability: string,
  preferLocal = false,
  preferCost = false,
  limit = 6
): string[] {
  const items: [number, string][] = [];
  Object.keys(PROVIDERS).forEach((pid) => {
    try {
      const s = scoreProvider(pid, capability, preferLocal, preferCost);
      if (s !== Infinity) items.push([s, pid]);
    } catch (e) {
      // ignore
    }
  });
  items.sort((a, b) => a[0] - b[0]);
  return items.slice(0, limit).map((x) => x[1]);
}

// minimal frontend router call to your backend route endpoint
/**
 * Routes AI tasks to the most appropriate provider based on task type and preferences
 *
 * This function acts as the frontend interface to the backend routing system,
 * which intelligently selects between local models, cloud providers, and cost-optimized options.
 *
 * @param taskType - The type of AI task (e.g., 'chat', 'completion', 'embedding')
 * @param payload - Task-specific data and parameters
 * @param opts - Routing preferences and constraints
 * @param opts.preferLocal - Prioritize local/edge models when available
 * @param opts.preferCost - Optimize for cost efficiency over speed
 * @returns Promise resolving to routing result with provider selection and response
 * @throws {Error} When routing fails or no suitable provider is available
 *
 * @example
 * ```typescript
 * const result = await routeTaskFrontend('chat', {
 *   messages: [{ role: 'user', content: 'Hello!' }],
 *   model: 'gpt-4'
 * }, { preferLocal: true });
 * ```
 */
export async function routeTaskFrontend(
  taskType: string,
  payload: unknown,
  opts?: { preferLocal?: boolean; preferCost?: boolean }
) {
  const routingResponse = await fetch('/api/route_task', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ task_type: taskType, payload, opts }),
  });
  return await routingResponse.json();
}

export default {
  topProvidersFor,
  updateMetricsFromBackend,
  routeTaskFrontend,
};
