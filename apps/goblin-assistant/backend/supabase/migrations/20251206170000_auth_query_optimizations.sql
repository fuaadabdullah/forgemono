-- Database Query Optimization Migration for Auth System
-- Created: 2025-12-06
-- Adds indexes and optimizations for better query performance

-- Add index on expires_at for user role assignments (used in _get_user_roles)
CREATE INDEX IF NOT EXISTS ix_user_role_assignments_expires_at ON user_role_assignments(expires_at);

-- Add composite index for user role queries (user_id + expires_at)
CREATE INDEX IF NOT EXISTS ix_user_role_assignments_user_expires ON user_role_assignments(user_id, expires_at);

-- Add index on token_version for user table (used in token validation)
CREATE INDEX IF NOT EXISTS ix_app_users_token_version ON app_users(token_version);

-- Add composite index for session queries (user_id + revoked + expires_at)
CREATE INDEX IF NOT EXISTS ix_user_sessions_user_revoked_expires ON user_sessions(user_id, revoked, expires_at);

-- Add index on last_active for session cleanup queries
CREATE INDEX IF NOT EXISTS ix_user_sessions_last_active ON user_sessions(last_active);

-- Add partial index for active sessions only (more efficient for common queries)
CREATE INDEX IF NOT EXISTS ix_user_sessions_active_only ON user_sessions(user_id, last_active DESC)
WHERE revoked = false AND (expires_at IS NULL OR expires_at > now());

-- Add index on audit logs for time-based queries
CREATE INDEX IF NOT EXISTS ix_audit_logs_created_at_action ON audit_logs(created_at DESC, action);

-- Add index on audit logs for actor-based queries
CREATE INDEX IF NOT EXISTS ix_audit_logs_actor_created ON audit_logs(actor_id, created_at DESC);

-- Optimize the _get_user_roles query by ensuring the join is efficient
-- The existing indexes should handle this, but let's ensure the query plan is optimal

-- Add a comment for future optimization reference
COMMENT ON INDEX ix_user_role_assignments_expires_at IS 'Optimizes role expiration queries in _get_user_roles method';
COMMENT ON INDEX ix_user_sessions_active_only IS 'Optimizes active session queries with partial index for better performance';
