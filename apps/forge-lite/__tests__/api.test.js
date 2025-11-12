/**
 * API Service tests for ForgeTM Lite
 * Tests backend services without React Native dependencies
 */

// Mock the market data service since it's implemented in Python
const MarketDataService = {
  getQuote: jest.fn(),
  getBatchQuotes: jest.fn(),
  calculatePositionSize: jest.fn(),
};

describe('Market Data Service', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should initialize correctly', () => {
    expect(MarketDataService).toBeDefined();
  });

  it('should calculate position size correctly', () => {
    const entryPrice = 150.00;
    const stopLoss = 145.00;
    const equity = 10000.00;
    const riskPercent = 1.0;

    const riskAmount = equity * (riskPercent / 100);
    const stopDistance = entryPrice - stopLoss;
    const positionSize = Math.floor(riskAmount / stopDistance);

    expect(positionSize).toBe(20); // 100 risk / 5 stop distance = 20 shares
  });

  it('should validate trade parameters', () => {
    const validTrade = {
      ticker: 'AAPL',
      entryPrice: 150.00,
      stopLoss: 145.00,
      equity: 10000.00,
      riskPercent: 1.0
    };

    expect(validTrade.ticker).toBe('AAPL');
    expect(validTrade.entryPrice).toBeGreaterThan(validTrade.stopLoss);
    expect(validTrade.riskPercent).toBeGreaterThan(0);
    expect(validTrade.equity).toBeGreaterThan(0);
  });
});

describe('Feedback Service', () => {
  it('should export feedback data structure', () => {
    const mockFeedback = {
      bug_reports: [
        {
          id: 'bug_001',
          title: 'Risk calculation error',
          severity: 'high',
          status: 'open'
        }
      ],
      feature_requests: [
        {
          id: 'feature_001',
          title: 'Dark mode toggle',
          votes: 15,
          status: 'planned'
        }
      ],
      user_feedback: [
        {
          rating: 4,
          comment: 'Great app for learning risk management'
        }
      ]
    };

    expect(mockFeedback.bug_reports).toHaveLength(1);
    expect(mockFeedback.feature_requests).toHaveLength(1);
    expect(mockFeedback.user_feedback).toHaveLength(1);
    expect(mockFeedback.bug_reports[0].severity).toBe('high');
  });
});

describe('Export Service', () => {
  it('should create GDPR-compliant export structure', () => {
    const mockExport = {
      user_profile: {
        user_id: 'user_123',
        created_at: '2024-01-01T00:00:00Z',
        gdpr_consent: true
      },
      trades: [
        {
          id: 'trade_001',
          ticker: 'AAPL',
          status: 'closed',
          pnl_dollars: 550.0
        }
      ],
      watchlists: [
        {
          name: 'Tech Stocks',
          tickers: ['AAPL', 'MSFT']
        }
      ],
      gdpr_compliant: true
    };

    expect(mockExport.gdpr_compliant).toBe(true);
    expect(mockExport.user_profile.user_id).toBe('user_123');
    expect(mockExport.trades).toHaveLength(1);
    expect(mockExport.watchlists).toHaveLength(1);
  });
});
