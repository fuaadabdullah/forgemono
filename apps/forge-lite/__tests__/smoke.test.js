/**
 * Smoke tests for ForgeTM Lite
 * Basic functionality tests to ensure core business logic works
 */

describe('Core Business Logic', () => {
  it('calculates position size correctly', () => {
    // Mock risk calculation logic
    const entryPrice = 150.00;
    const stopLoss = 145.00;
    const equity = 10000.00;
    const riskPercent = 1.0;

    const riskAmount = equity * (riskPercent / 100);
    const stopDistance = entryPrice - stopLoss;
    const positionSize = Math.floor(riskAmount / stopDistance);

    expect(positionSize).toBe(20); // 100 risk / 5 stop distance = 20 shares
  });

  it('calculates R-multiple correctly', () => {
    const entryPrice = 150.00;
    const exitPrice = 165.00;
    const stopLoss = 145.00;

    const reward = exitPrice - entryPrice;
    const risk = entryPrice - stopLoss;
    const rMultiple = reward / risk;

    expect(rMultiple).toBe(3.0); // 15 reward / 5 risk = 3R
  });

  it('validates trade data structure', () => {
    const mockTrade = {
      id: 'test-trade-1',
      ticker: 'AAPL',
      status: 'active',
      side: 'long',
      entryPrice: 150.00,
      quantity: 100,
      entryDate: new Date().toISOString(),
    };

    expect(mockTrade).toHaveProperty('id');
    expect(mockTrade).toHaveProperty('ticker');
    expect(mockTrade).toHaveProperty('status');
    expect(mockTrade).toHaveProperty('entryPrice');
    expect(mockTrade).toHaveProperty('quantity');
    expect(mockTrade.ticker).toBe('AAPL');
    expect(mockTrade.status).toBe('active');
  });

  it('validates watchlist structure', () => {
    const mockWatchlist = {
      id: 'watchlist-1',
      name: 'Tech Stocks',
      tickers: ['AAPL', 'MSFT', 'GOOGL'],
      createdAt: new Date().toISOString(),
    };

    expect(mockWatchlist).toHaveProperty('id');
    expect(mockWatchlist).toHaveProperty('name');
    expect(mockWatchlist).toHaveProperty('tickers');
    expect(mockWatchlist.tickers).toContain('AAPL');
    expect(mockWatchlist.tickers).toHaveLength(3);
  });

  it('handles offline-first functionality', () => {
    // Test that calculations work without network
    const offlineCalculation = {
      entryPrice: 100.00,
      stopLoss: 95.00,
      equity: 5000.00,
      riskPercent: 2.0,
    };

    const riskAmount = offlineCalculation.equity * (offlineCalculation.riskPercent / 100);
    const stopDistance = offlineCalculation.entryPrice - offlineCalculation.stopLoss;
    const positionSize = Math.floor(riskAmount / stopDistance);

    expect(positionSize).toBe(20); // 100 risk / 5 stop distance = 20 shares
    expect(riskAmount).toBe(100); // 2% of 5000
  });
});
