export type WatchlistItem = {
  symbol: string;
  name?: string;
  price?: number;
  change?: number;
  changePercent?: number;
  volume?: number;
  lastUpdated?: Date;
};

export type MarketQuote = {
  symbol: string;
  price: number;
  change: number;
  changePercent: number;
  volume: number;
  timestamp: Date;
};

export type Candle = {
  t: number; // epoch ms
  o: number;
  h: number;
  l: number;
  c: number;
  v: number;
};

export type Trade = {
  id: string;
  symbol: string;
  direction: 'long' | 'short';
  entry: number;
  stop: number;
  target?: number;
  riskAmount: number;
  positionSize: number;
  status: 'planned' | 'active' | 'closed' | 'cancelled';
  pnl?: number;
  rMultiple?: number;
  notes?: string;
  setup?: string;
  createdAt: Date;
  closedAt?: Date;
};

export type RiskCalcParams = {
  entry: number;
  stop: number;
  equity: number;
  riskPercent: number;
  target?: number;
  direction: 'long' | 'short';
};

export type RiskCalcResult = {
  direction: 'long' | 'short';
  riskPerShare: number;
  riskAmount: number;
  positionSize: number;
  rMultipleStop: number;
  rMultipleTarget?: number;
  projectedPnl?: number;
};
