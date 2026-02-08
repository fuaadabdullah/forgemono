# Production Configuration Guide

## OpenTelemetry Observability Stack

Goblin Assistant uses OpenTelemetry for unified observability across distributed services.

### Environment Variables

Add these to your `backend/.env` file:

```bash
# OpenTelemetry Configuration
OTLP_ENDPOINT=http://localhost:4317  # OTLP collector endpoint
ENABLE_OPENTELEMETRY=true           # Enable OpenTelemetry instrumentation
ENVIRONMENT=production              # Environment name for resource attributes

# Logging
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL

# CORS Configuration (comma-separated list)
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com,https://www.yourdomain.com

# Rate Limiting (optional, defaults in rate_limiter.py)
# RATELIMIT_ENABLED=true
```

### OpenTelemetry Components

#### 1. Auto-Instrumentation

OpenTelemetry automatically instruments:
- **FastAPI**: HTTP requests, responses, and routing
- **HTTPX**: External API calls to LLM providers
- **SQLAlchemy**: Database operations
- **Redis**: Cache and session operations

#### 2. Distributed Tracing

Traces flow from:
- Cloudflare Edge Workers → Backend API → LLM Providers
- Frontend requests → Backend API → Database/Redis

**Trace Context Headers:**
- `traceparent`: W3C trace context
- `tracestate`: Vendor-specific trace state
- `X-Correlation-ID`: Human-readable correlation ID

#### 3. Metrics Collection

**Service Level Objectives (SLOs):**
- Chat response time: < 2s (p95) - 99% target
- Auth success rate: > 99.9% - 99.9% target
- LLM provider availability: > 99.5% - 99.5% target
- API availability: > 99.9% - 99.9% target

**Business Metrics:**
- Daily/Monthly Active Users (DAU/MAU)
- Cost per request by provider
- Token usage by model
- Feature usage tracking

#### 4. Structured Logging

Logs include OpenTelemetry trace context for correlation:

```json

{
  "timestamp": "2025-12-06T10:30:45.123Z",
  "level": "INFO",
  "message": "request_completed",
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
  "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
  "span_id": "00f067aa0ba902b7",
  "method": "POST",
  "path": "/chat/completions",
  "status_code": 200,
  "duration_ms": 1234.56
}
```

### OTLP Collector Setup

For production, deploy an OpenTelemetry Collector to receive and export telemetry:

```yaml
# docker-compose.yml
version: '3.8'
services:
  otel-collector:
    image: otel/opentelemetry-collector-contrib:latest
    ports:
      - "4317:4317"  # OTLP gRPC
      - "4318:4318"  # OTLP HTTP
    volumes:
      - ./otel-collector-config.yaml:/etc/otel-collector-config.yaml
```

**Collector Configuration:**
```yaml

receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318

exporters:
  jaeger:
    endpoint: jaeger:14268/api/traces
  prometheus:
    endpoint: 0.0.0.0:8889
  loki:
    endpoint: <http://loki:3100/loki/api/v1/push>

service:
  pipelines:
    traces:
      receivers: [otlp]
      exporters: [jaeger]
    metrics:
      receivers: [otlp]
      exporters: [prometheus]
    logs:
      receivers: [otlp]
      exporters: [loki]
```

### SLO Monitoring

Monitor SLO compliance using the `/metrics` endpoint:

```prometheus
# SLO Compliance Ratios (0.0 to 1.0)
slo_chat_response_time_compliance_ratio{target="0.99"} 0.995
slo_auth_success_rate_compliance_ratio{target="0.999"} 0.9995
slo_llm_provider_availability_compliance_ratio{target="0.995"} 0.997
slo_api_availability_compliance_ratio{target="0.999"} 0.9998

# SLI Counters
sli_chat_response_time_sli_good_events_total 9995
sli_chat_response_time_sli_total_events_total 10000
```

### Alerting Rules

Example Prometheus alerting rules:

```yaml

groups:

  - name: goblin_assistant_slos
    rules:

      - alert: ChatResponseTimeSLOViolation
        expr: slo_chat_response_time_compliance_ratio < 0.99
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Chat response time SLO violated"
          description: "Chat responses are slower than 2s p95 target"

      - alert: AuthSuccessRateSLOViolation
        expr: slo_auth_success_rate_compliance_ratio < 0.999
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Auth success rate SLO violated"
          description: "Authentication success rate below 99.9% target"
```

## LLM Runtime (Production)

Important: Production LLM runtimes (e.g., Ollama, llama.cpp instances) must run remotely on the Kamatera managed hosts. Do NOT host production LLM runtimes on the application host.

Add the following production-only environment variables and point them to your Kamatera runtime endpoints:

```bash
# Kamatera LLM runtime
KAMATERA_HOST=kamatera.example
KAMATERA_LLM_URL=https://llm.kamatera.example
KAMATERA_LLM_API_KEY=your-kamatera-llm-api-key
```

For local development you may still run a local LLM proxy (ollama/llama.cpp) behind `USE_LOCAL_LLM=true`, but ensure `USE_LOCAL_LLM` is false or unset in production `.env` on Kamatera.


## Middleware Features

### 1. Rate Limiting (slowapi)

**Default Limits:**
- Auth endpoints: 10 requests/minute
- Chat endpoints: 30 requests/minute
- Health endpoints: 60 requests/minute
- General API: 100 requests/minute

**How it works:**
- Tracks by client IP address
- Returns 429 status when exceeded
- Includes `retry_after` in response

**Response format:**
```json

{
  "error": "rate_limit_exceeded",
  "message": "Rate limit exceeded: 10 per 1 minute",
  "retry_after": 45
}
```

### 2. Structured JSON Logging

**Features:**

- All logs in JSON format for easy parsing
- Automatic request/response logging
- Correlation IDs for request tracing
- Error tracking with stack traces

**Log format:**

```json
{
  "timestamp": "2025-12-02T10:30:45.123Z",
  "level": "INFO",
  "logger": "goblin_assistant",
  "message": "request_completed",
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
  "method": "POST",
  "path": "/chat/completions",
  "status_code": 200,
  "duration_ms": 1234.56
}
```

**Correlation ID:**
- Added to every request automatically
- Returned in `X-Correlation-ID` response header
- Use for debugging across distributed systems

### 3. Prometheus Metrics

**Metrics endpoint:** `GET /metrics`

**Available metrics:**

```prometheus

# HTTP Metrics
http_requests_total{method="POST",endpoint="/chat/completions",status_code="200"} 42
http_request_duration_seconds_bucket{method="POST",endpoint="/chat/completions",le="1.0"} 35
http_requests_in_progress{method="POST",endpoint="/chat/completions"} 2
http_errors_total{method="POST",endpoint="/chat/completions",error_type="TimeoutError"} 1

# Business Metrics
chat_completions_total{provider="openai",model="gpt-4"} 100
chat_completion_tokens_total{provider="openai",model="gpt-4",token_type="prompt"} 50000
chat_completion_errors_total{provider="anthropic",error_type="rate_limit"} 5
provider_latency_seconds{provider="openai",operation="chat_completion"} 1.234

# Health Metrics
service_health_status{service_name="chroma"} 1
service_health_status{service_name="sandbox"} 0
```

**Custom metric tracking in code:**

```python
from middleware.metrics import (
    chat_completions_total,
    chat_completion_tokens_total,
    provider_latency_seconds
)

# Track completion
chat_completions_total.labels(
    provider="openai",
    model="gpt-4"
).inc()

# Track tokens
chat_completion_tokens_total.labels(
    provider="openai",
    model="gpt-4",
    token_type="prompt"
).inc(response.usage.prompt_tokens)

# Track latency
provider_latency_seconds.labels(
    provider="openai",
    operation="chat_completion"
).observe(duration)
```

### 4. Load Testing (Locust)

**Run load tests:**

```bash

# Install dependencies
pip install -r backend/requirements.txt

# Start backend
cd apps/goblin-assistant/backend
uvicorn main:app --host 0.0.0.0 --port 8001

# Run load test with Web UI
locust -f backend/tests/load_test.py --host=<http://localhost:8001>

# Open browser to http://localhost:8089

# Set number of users and spawn rate

# Headless mode (CLI only)
locust -f backend/tests/load_test.py --host=<http://localhost:8001> \
       --users 10 --spawn-rate 2 --run-time 60s --headless
```

**Performance targets:**

- Health checks: < 100ms p95, 100 RPS
- Chat completions: < 2s p95, 10 RPS
- Auth login: < 500ms p95, 20 RPS

**Test scenarios:**

1. `health_check` (10x weight) - Basic health endpoint
2. `health_all` (8x) - Detailed health with all services
3. `health_chroma` (5x) - ChromaDB health check
4. `health_sandbox` (3x) - Sandbox health check
5. `get_models` (2x) - List available models
6. `chat_completion` (1x) - Full chat completion (expensive)
7. `get_settings` (2x) - Retrieve settings
8. `login` (1x) - Authentication

## Monitoring Setup

### Sentry Error Tracking

**1. Install Sentry SDK:**

```bash
pip install sentry-sdk
```

**2. Configure Sentry:**
```python

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

sentry_sdk.init(
    dsn="your-sentry-dsn",
    environment="production",
    integrations=[FastApiIntegration()],
    traces_sample_rate=1.0,
)
```

**3. Environment Variables:**

```bash
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
SENTRY_ENVIRONMENT=production
```

### Error Monitoring

Sentry automatically captures:
- Unhandled exceptions
- Performance issues
- User feedback
- Release tracking

**Benefits:**
- Real-time error alerting
- Performance monitoring
- User impact analysis
- Release health tracking

## Deployment Checklist

- [ ] Set `CORS_ORIGINS` to production domains
- [ ] Set `LOG_LEVEL=INFO` (or WARNING for production)
- [ ] Configure Sentry error tracking
- [ ] Set up automated health checks
- [ ] Configure rate limit thresholds for your scale
- [ ] Monitor error rates for first 24 hours

## Testing the Setup

**1. Check rate limiting:**
```bash

# Should return 429 after 10 requests
for i in {1..15}; do
  curl -X POST <http://localhost:8001/auth/login> \
    -H "Content-Type: application/json" \
    -d '{"email":"test@example.com","password":"test"}'
  sleep 1
done
```

**2. Check structured logs:**

```bash
# Start server and watch logs
uvicorn main:app --host 0.0.0.0 --port 8001 | jq

# Should see JSON formatted logs with correlation_id
```

**3. Check Sentry error tracking:**
```bash

# Trigger a test error
curl -X GET <http://localhost:8001/test-error>

# Should see error appear in Sentry dashboard
```

**4. Run load test:**

```bash
locust -f backend/tests/load_test.py --host=http://localhost:8001 \
       --users 10 --spawn-rate 2 --run-time 30s --headless

# Should complete without errors
# Check that performance targets are met
```

## Production Recommendations

1. **Rate Limiting:**
   - Tune limits based on your infrastructure
   - Consider Redis-based rate limiting for distributed systems
   - Add API key-based limits (not just IP)

2. **Logging:**
   - Send logs to centralized aggregation service
   - Set log retention policies
   - Create alerts on ERROR level logs

3. **Error Monitoring:**
   - Configure Sentry alerts for critical errors
   - Set up release tracking for deployment monitoring
   - Monitor error rates and user impact

4. **Load Testing:**
   - Run regular load tests on staging
   - Test disaster recovery scenarios
   - Validate auto-scaling configuration

5. **Security:**
   - Enable HTTPS in production
   - Use reverse proxy (nginx/traefik) for additional protection
   - Implement API key authentication for sensitive endpoints
   - Add request size limits
   - Enable CORS only for trusted origins
<!-- Canonical copy for backend docs (moved from apps/goblin-assistant/PRODUCTION_MONITORING.md) -->
<!-- Please edit content only in apps/goblin-assistant/backend/docs/PRODUCTION_MONITORING.md -->

```markdown

# Production Configuration Guide

## Environment Variables

Add these to your `backend/.env` file:

```bash
# Logging
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL

... (truncated for brevity; full content mirrored from root file)

```
