/* Minimal API client for Forge Lite */

export type RiskCalcRequest = {
  entry: number;
  stop: number;
  equity: number;
  risk_pct: number; // 0..1
  target?: number;
  direction?: 'long' | 'short';
};

export type RiskCalcResponse = {
  direction: 'long' | 'short';
  risk_per_share: number;
  risk_amount: number;
  position_size: number;
  r_multiple_stop: number;
  r_multiple_target?: number;
  projected_pnl?: number;
};

const API_URL = process.env.EXPO_PUBLIC_API_URL ?? 'http://localhost:8000';

async function http<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    headers: { 'Content-Type': 'application/json', ...(init?.headers || {}) },
    ...init,
  });
  if (!res.ok) {
    let detail: unknown;
    try {
      detail = await res.json();
    } catch {
      detail = await res.text();
    }
    throw new Error(`API ${res.status}: ${JSON.stringify(detail)}`);
  }
  return (await res.json()) as T;
}

export const api = {
  risk: {
    calc: (body: RiskCalcRequest) =>
      http<RiskCalcResponse>('/risk/calc', {
        method: 'POST',
        body: JSON.stringify(body),
      }),
  },
};

export default api;

