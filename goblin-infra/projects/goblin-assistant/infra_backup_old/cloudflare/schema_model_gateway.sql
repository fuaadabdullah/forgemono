-- Model Gateway D1 Schema
-- Tracks inference requests, costs, and provider health

-- Inference logs table (tracks every AI model request)
CREATE TABLE IF NOT EXISTS inference_logs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
  request_id TEXT NOT NULL,
  user_id TEXT,
  model TEXT NOT NULL,
  provider TEXT NOT NULL,
  endpoint TEXT NOT NULL,
  prompt_tokens INTEGER DEFAULT 0,
  completion_tokens INTEGER DEFAULT 0,
  total_tokens INTEGER DEFAULT 0,
  cost_usd REAL DEFAULT 0.0,
  latency_ms INTEGER,
  status TEXT, -- 'success', 'failed', 'timeout'
  error_message TEXT,
  routing_strategy TEXT,
  was_cached BOOLEAN DEFAULT 0
);

-- Indexes for fast queries
CREATE INDEX IF NOT EXISTS idx_inference_user_timestamp
  ON inference_logs(user_id, timestamp);

CREATE INDEX IF NOT EXISTS idx_inference_provider_timestamp
  ON inference_logs(provider, timestamp);

CREATE INDEX IF NOT EXISTS idx_inference_model_timestamp
  ON inference_logs(model, timestamp);

CREATE INDEX IF NOT EXISTS idx_inference_status
  ON inference_logs(status, timestamp);

-- Provider health table (tracks endpoint availability)
CREATE TABLE IF NOT EXISTS provider_health (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  provider TEXT NOT NULL UNIQUE,
  endpoint TEXT NOT NULL,
  last_check DATETIME DEFAULT CURRENT_TIMESTAMP,
  is_healthy BOOLEAN DEFAULT 1,
  avg_latency_ms INTEGER DEFAULT 0,
  success_rate REAL DEFAULT 1.0,
  total_requests INTEGER DEFAULT 0,
  failed_requests INTEGER DEFAULT 0,
  last_error TEXT
);

CREATE INDEX IF NOT EXISTS idx_provider_health_check
  ON provider_health(provider, last_check);

-- Initialize provider health records
INSERT OR IGNORE INTO provider_health (provider, endpoint, is_healthy) VALUES
  ('ollama', 'http://localhost:11434', 1),
  ('llamacpp', 'http://localhost:8080', 1),
  ('kamatera', 'https://your-kamatera-server.com:8080', 1),
  ('openai', 'https://api.openai.com/v1', 1),
  ('anthropic', 'https://api.anthropic.com/v1', 1),
  ('groq', 'https://api.groq.com/openai/v1', 1);
