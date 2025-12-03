-- D1 Database Schema for Goblin Assistant
-- SQLite at the edge for structured data
-- User Preferences (stored at edge, fast access)
CREATE TABLE user_preferences (
    user_id TEXT PRIMARY KEY,
    theme TEXT DEFAULT 'dark',
    language TEXT DEFAULT 'en',
    model_preference TEXT DEFAULT 'gpt-4',
    temperature REAL DEFAULT 0.7,
    max_tokens INTEGER DEFAULT 2000,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
-- Audit Logs (security and compliance)
CREATE TABLE audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT,
    action TEXT NOT NULL,
    details TEXT,
    ip_address TEXT,
    user_agent TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);
-- Feature Flags (dynamic config at edge)
CREATE TABLE feature_flags (
    flag_name TEXT PRIMARY KEY,
    enabled BOOLEAN DEFAULT 0,
    rollout_percentage INTEGER DEFAULT 0,
    description TEXT,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
-- Session Store (optional, can also use KV)
CREATE TABLE sessions (
    session_token TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    expires_at DATETIME NOT NULL,
    last_activity DATETIME DEFAULT CURRENT_TIMESTAMP
);
-- API Usage Tracking (for billing/analytics)
CREATE TABLE api_usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT,
    endpoint TEXT,
    tokens_used INTEGER DEFAULT 0,
    cost_usd REAL DEFAULT 0,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);
-- Indexes for performance
CREATE INDEX idx_user_id ON audit_logs(user_id);
CREATE INDEX idx_timestamp ON audit_logs(timestamp);
CREATE INDEX idx_session_user ON sessions(user_id);
CREATE INDEX idx_session_expires ON sessions(expires_at);
CREATE INDEX idx_usage_user ON api_usage(user_id);
CREATE INDEX idx_usage_timestamp ON api_usage(timestamp);
-- Insert default feature flags
INSERT INTO feature_flags (
        flag_name,
        enabled,
        rollout_percentage,
        description
    )
VALUES ('api_enabled', 1, 100, 'Main API enabled'),
    (
        'rate_limiting_enabled',
        1,
        100,
        'Rate limiting enforcement'
    ),
    (
        'new_ui_enabled',
        0,
        10,
        'New UI rollout (10% of users)'
    ),
    (
        'experimental_features',
        0,
        0,
        'Experimental features (internal only)'
    );
