-- Create custom types
CREATE TYPE trade_status AS ENUM ('planned', 'active', 'closed', 'cancelled');
CREATE TYPE trade_side AS ENUM ('long', 'short');
CREATE TYPE journal_sentiment AS ENUM ('bullish', 'bearish', 'neutral');

-- Create trades table
CREATE TABLE trades (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  ticker TEXT NOT NULL,
  status trade_status NOT NULL DEFAULT 'planned',
  side trade_side NOT NULL,
  quantity INTEGER NOT NULL CHECK (quantity > 0),
  entry_price DECIMAL(10,2) NOT NULL CHECK (entry_price > 0),
  stop_loss DECIMAL(10,2),
  target_price DECIMAL(10,2),
  exit_price DECIMAL(10,2),
  entry_date TIMESTAMPTZ,
  exit_date TIMESTAMPTZ,
  risk_percent DECIMAL(4,2) DEFAULT 1.0 CHECK (risk_percent > 0 AND risk_percent <= 100),
  fees DECIMAL(8,2) DEFAULT 0.00,
  pnl_dollars DECIMAL(10,2),
  pnl_r_multiple DECIMAL(6,2),
  notes TEXT,
  tags TEXT[] DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create watchlists table
CREATE TABLE watchlists (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  description TEXT,
  tickers TEXT[] NOT NULL DEFAULT '{}',
  is_default BOOLEAN DEFAULT false,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(user_id, name)
);

-- Create journal_entries table
CREATE TABLE journal_entries (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  trade_id UUID REFERENCES trades(id) ON DELETE CASCADE,
  date TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  market_conditions TEXT,
  entry_reasoning TEXT,
  exit_reasoning TEXT,
  emotional_state TEXT,
  mistakes TEXT,
  lessons_learned TEXT,
  improvements TEXT,
  sentiment journal_sentiment,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create user_preferences table
CREATE TABLE user_preferences (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE UNIQUE,
  theme TEXT DEFAULT 'dark' CHECK (theme IN ('light', 'dark')),
  default_risk_percent DECIMAL(4,2) DEFAULT 1.0,
  notifications_enabled BOOLEAN DEFAULT true,
  data_export_frequency TEXT DEFAULT 'monthly' CHECK (data_export_frequency IN ('never', 'monthly', 'quarterly', 'yearly')),
  privacy_analytics BOOLEAN DEFAULT true,
  privacy_crash_reports BOOLEAN DEFAULT true,
  privacy_marketing BOOLEAN DEFAULT false,
  trading_default_broker TEXT DEFAULT 'none',
  trading_calculation_method TEXT DEFAULT 'percentage_of_equity' CHECK (trading_calculation_method IN ('percentage_of_equity', 'fixed_dollar', 'fixed_percentage')),
  trading_journal_required BOOLEAN DEFAULT true,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create feedback table for user feedback
CREATE TABLE feedback (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
  type TEXT NOT NULL CHECK (type IN ('bug_report', 'feature_request', 'general_feedback', 'app_rating')),
  title TEXT,
  description TEXT,
  rating INTEGER CHECK (rating >= 1 AND rating <= 5),
  platform TEXT CHECK (platform IN ('ios', 'android', 'web')),
  app_version TEXT,
  status TEXT DEFAULT 'open' CHECK (status IN ('open', 'in_progress', 'resolved', 'closed')),
  priority TEXT DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high', 'critical')),
  votes INTEGER DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX idx_trades_user_id ON trades(user_id);
CREATE INDEX idx_trades_status ON trades(status);
CREATE INDEX idx_trades_ticker ON trades(ticker);
CREATE INDEX idx_trades_created_at ON trades(created_at);

CREATE INDEX idx_watchlists_user_id ON watchlists(user_id);

CREATE INDEX idx_journal_entries_user_id ON journal_entries(user_id);
CREATE INDEX idx_journal_entries_trade_id ON journal_entries(trade_id);
CREATE INDEX idx_journal_entries_date ON journal_entries(date);

CREATE INDEX idx_feedback_type ON feedback(type);
CREATE INDEX idx_feedback_status ON feedback(status);
CREATE INDEX idx_feedback_created_at ON feedback(created_at);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Add updated_at triggers
CREATE TRIGGER update_trades_updated_at BEFORE UPDATE ON trades FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_watchlists_updated_at BEFORE UPDATE ON watchlists FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_journal_entries_updated_at BEFORE UPDATE ON journal_entries FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_user_preferences_updated_at BEFORE UPDATE ON user_preferences FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_feedback_updated_at BEFORE UPDATE ON feedback FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert default watchlist for new users
CREATE OR REPLACE FUNCTION create_default_watchlist()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO watchlists (user_id, name, description, tickers, is_default)
  VALUES (
    NEW.id,
    'My Watchlist',
    'Default watchlist for tracking stocks',
    ARRAY['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA'],
    true
  );

  INSERT INTO user_preferences (user_id)
  VALUES (NEW.id);

  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION create_default_watchlist();
