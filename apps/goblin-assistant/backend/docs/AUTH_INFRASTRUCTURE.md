# Authentication System Architecture

## Overview

The Goblin Assistant authentication system provides resilient, scalable user authentication with support for passkey/WebAuthn authentication, JWT tokens, and comprehensive email validation.

## Challenge Storage

The auth system uses a **resilient challenge storage** mechanism with automatic fallback:

### Primary Storage: Redis

- **Purpose**: Distributed, shared challenge storage across multiple instances
- **TTL**: Configurable via `CHALLENGE_EXPIRE_MINUTES` (default: 5 minutes)
- **Connection**: Configurable via `REDIS_URL` environment variable

### Fallback Storage: In-Memory

- **Purpose**: Single-instance fallback when Redis is unavailable
- **Limitations**: Not suitable for multi-instance deployments
- **Safety**: Automatically activates when Redis connection fails

### Environment-Specific Behavior

#### Development

- Redis optional (fallback enabled by default)
- Debug logging enabled via `DEBUG_AUTH=true`
- Single instance assumed unless `INSTANCE_COUNT > 1`

#### Staging

- Redis recommended but not strictly required
- Fallback allowed for testing resilience
- Multi-instance support with warnings

#### Production

- **Redis REQUIRED** for multi-instance deployments (`INSTANCE_COUNT > 1`)
- Fallback mode triggers **CRITICAL alerts** when active
- Strict health checks and monitoring

## Configuration

### Environment Variables

```bash
# Environment
ENVIRONMENT=production|staging|development
INSTANCE_COUNT=1

# Redis
REDIS_URL=redis://localhost:6379
REDIS_TIMEOUT=5
ALLOW_MEMORY_FALLBACK=false

# Authentication
CHALLENGE_TTL=300
DEBUG_AUTH=false
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Email Validation
REQUIRE_EMAIL_VALIDATION=true
ALLOW_DISPOSABLE_EMAILS=false
```

### Configuration Validation

The system validates configuration on startup:

- **Production**: Requires `DATABASE_URL`
- **All Environments**: Memory fallback disabled by default (Redis required)
- **Development**: Can enable memory fallback for local development

## Email Validation

### Pydantic EmailStr Integration

The system uses `pydantic[email]` for robust email validation:

```python

from pydantic import BaseModel, EmailStr, field_validator

class UserRegistration(BaseModel):
    email: EmailStr
    username: str

    @field_validator("email")
    @classmethod
    def validate_email_domain(cls, v: str) -> str:
        """Block disposable email domains"""
        disposable_domains = ["tempmail.com", "10minutemail.com", "guerrillamail.com"]
        domain = v.split("@")[1].lower()
        if domain in disposable_domains:
            raise ValueError("Disposable email domains not allowed")
        return v
```

### Blocked Domains

The system blocks common disposable email domains:

- `tempmail.com`
- `10minutemail.com`
- `guerrillamail.com`
- `mailinator.com`
- And others (configurable)

## Health Checks

### Comprehensive Health Endpoint

**Endpoint**: `GET /health/`

Returns environment-aware health status:

```json
{
  "status": "healthy|degraded|unhealthy",
  "timestamp": "2025-12-05T10:30:00Z",
  "environment": "production",
  "components": {
    "redis": {
      "status": "healthy",
      "fallback_active": false,
      "safe_for_environment": true
    },
    "database": {
      "status": "healthy"
    },
    "auth_routes": {
      "status": "healthy",
      "count": 8,
      "routes": ["/auth/login", "/auth/register", ...]
    },
    "configuration": {
      "status": "healthy",
      "environment": "production",
      "multi_instance": false
    }
  }
}
```

### Component Checks

1. **Redis**: Connection status, fallback mode, environment safety
2. **Database**: Connectivity and basic query execution
3. **Auth Routes**: Route registration verification
4. **Configuration**: Environment-specific validation

### Status Determination

- **Healthy**: All components healthy
- **Degraded**: Some components degraded (Redis fallback, etc.)
- **Unhealthy**: Critical components failing

## Dependencies

### Required Packages

```bash

pip install pydantic[email] redis fastapi uvicorn
```

### Optional Packages

```bash
pip install pytest pytest-asyncio  # For testing
```

## Monitoring & Alerting

### Key Metrics to Monitor

1. **Redis Fallback Mode**
   - Alert: `CRITICAL` in production multi-instance
   - Query: `GET /health/` → `components.redis.fallback_active`

2. **Auth Route Count**
   - Alert: `WARNING` if count = 0
   - Query: `GET /health/` → `components.auth_routes.count`

3. **Configuration Issues**
   - Alert: `CRITICAL` if status = "unhealthy"
   - Query: `GET /health/` → `components.configuration.status`

### Recommended Alerts

```yaml

# Redis fallback in production

- condition: components.redis.fallback_active == true AND environment == production
  severity: critical
  message: "Redis fallback active in production environment"

# Missing auth routes

- condition: components.auth_routes.count == 0
  severity: warning
  message: "No authentication routes registered"

# Configuration validation failure

- condition: components.configuration.status == unhealthy
  severity: critical
  message: "Configuration validation failed"
```

## Testing

### Resilience Tests

Run comprehensive tests for fallback scenarios:

```bash
# Test Redis failure and recovery
pytest tests/test_auth_resilience.py::TestAuthResilience::test_redis_fallback_activates
pytest tests/test_auth_resilience.py::TestAuthResilience::test_redis_recovery

# Test email validation
pytest tests/test_auth_resilience.py::TestEmailValidation

# Test configuration validation
pytest tests/test_auth_resilience.py::TestConfigurationValidation
```

### Health Check Tests

```bash

# Test health endpoint
pytest tests/test_auth_resilience.py::TestHealthCheckIntegration
```

## Deployment Checklist

### Pre-Deployment

- [ ] Install `pydantic[email]` and `redis` packages
- [ ] Configure `REDIS_URL` for production
- [ ] Set `ENVIRONMENT=production`
- [ ] Configure `INSTANCE_COUNT` if multi-instance
- [ ] Run dependency check: `python scripts/check_dependencies.py`
- [ ] Test health endpoint: `GET /health/`

### Production Validation

- [ ] Health check returns `"status": "healthy"`
- [ ] Redis component shows `"fallback_active": false`
- [ ] Auth routes count > 0
- [ ] Configuration validation passes

### Monitoring Setup

- [ ] Configure alerts for Redis fallback in production
- [ ] Set up health check monitoring (every 30s)
- [ ] Enable structured logging for auth operations
- [ ] Configure log aggregation for error tracking

## Troubleshooting

### Redis Connection Issues

**Symptom**: Health check shows Redis unhealthy

**Solutions**:

1. Verify `REDIS_URL` configuration
2. Check Redis server connectivity
3. Confirm Redis service is running
4. Check firewall/network connectivity

### Memory Fallback Disabled

**Symptom**: `ConnectionError` when Redis unavailable and `ALLOW_MEMORY_FALLBACK=false`

**Impact**: System fails fast, preventing unsafe operation

**Solutions**:

1. **Immediate**: Ensure Redis is available and accessible
2. **Development**: Set `ALLOW_MEMORY_FALLBACK=true` for local testing
3. **Production**: Redis is always required for multi-instance safety

### Email Validation Failures

**Symptom**: EmailStr validation errors

**Solutions**:

1. Verify `pydantic[email]` is installed
2. Check `email-validator` package availability
3. Review disposable domain list in validators

### Configuration Validation Errors

**Symptom**: Configuration component unhealthy

**Common Issues**:

- Missing `DATABASE_URL` in production
- Memory fallback enabled in multi-instance production

**Solutions**:

1. Review environment variables
2. Check configuration validation logic
3. Update deployment configuration

## Security Considerations

### Challenge Storage Security

- Challenges expire within 5 minutes
- Redis encryption recommended for production
- Memory fallback disabled by default (Redis required for all environments)
- No sensitive data stored in memory-only mode

### Email Validation Security

- Blocks disposable email domains
- Prevents temporary email abuse
- Validates email format using RFC standards

### JWT Security

- Use strong, randomly generated `JWT_SECRET_KEY`
- Configure appropriate token expiration
- Implement token refresh mechanisms if needed

## Performance Considerations

### Redis Performance

- Connection pooling recommended for high load
- Monitor Redis latency and connection counts
- Consider Redis cluster for high availability

### Health Check Performance

- Health checks are lightweight (sub-second)
- Cached results acceptable for monitoring
- Avoid expensive operations in health checks

### Email Validation Performance

- Domain validation is fast (in-memory list)
- Consider caching for high-volume registration
- Async validation for bulk operations
