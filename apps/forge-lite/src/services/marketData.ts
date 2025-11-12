import { Candle, MarketQuote } from '../types';
const API_URL = process.env.EXPO_PUBLIC_API_URL || 'http://localhost:8000';

class MarketDataService {
  private ohlcCache = new Map<string, { data: Candle[]; timestamp: number }>();
  private readonly OHLC_TTL = 2 * 60 * 1000; // 2 minutes
  private cache = new Map<string, { data: MarketQuote; timestamp: number }>();
  private readonly CACHE_DURATION = 5 * 60 * 1000; // 5 minutes

  async getQuote(symbol: string): Promise<MarketQuote | null> {
    // Check cache first
    const cached = this.cache.get(symbol);
    if (cached && Date.now() - cached.timestamp < this.CACHE_DURATION) {
      return cached.data;
    }

    try {
      // In a real app, this would call the backend API
      // For now, return mock data
      const mockQuote: MarketQuote = {
        symbol,
        price: Math.random() * 1000 + 100,
        change: (Math.random() - 0.5) * 20,
        changePercent: (Math.random() - 0.5) * 5,
        volume: Math.floor(Math.random() * 1000000),
        timestamp: new Date(),
      };

      this.cache.set(symbol, { data: mockQuote, timestamp: Date.now() });
      return mockQuote;
    } catch (error) {
      console.error(`Failed to fetch quote for ${symbol}:`, error);
      return null;
    }
  }

  async getQuotes(symbols: string[]): Promise<Record<string, MarketQuote | null>> {
    const results: Record<string, MarketQuote | null> = {};

    // Batch requests for better performance
    const promises = symbols.map(async (symbol) => {
      results[symbol] = await this.getQuote(symbol);
    });

    await Promise.all(promises);
    return results;
  }

  async getOHLC(symbol: string, timeframe: '1D' | '1W' | '1M'): Promise<Candle[]> {
    try {
      const key = `${symbol}:${timeframe}`;
      const cached = this.ohlcCache.get(key);
      if (cached && Date.now() - cached.timestamp < this.OHLC_TTL) {
        return cached.data;
      }
      const res = await fetch(`${API_URL}/market/ohlc?symbol=${encodeURIComponent(symbol)}&timeframe=${timeframe}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      const candles = Array.isArray(data) ? (data as Candle[]) : [];
      this.ohlcCache.set(key, { data: candles, timestamp: Date.now() });
      return candles;
    } catch (e) {
      console.warn('getOHLC failed', e);
      return [];
    }
  }

  clearCache(): void {
    this.cache.clear();
  }
}

export const marketDataService = new MarketDataService();
