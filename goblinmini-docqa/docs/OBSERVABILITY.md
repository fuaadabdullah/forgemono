# Goblin DocQA Observability Setup

This document describes the Prometheus metrics and alerting setup for Goblin DocQA.

## Metrics

The service exposes comprehensive Prometheus metrics at `/metrics`:

### Queue Metrics

- `goblin_docqa_queue_length` - Current job queue length
- `goblin_docqa_queue_max_size` - Maximum queue capacity

### Inference Metrics

- `goblin_docqa_inference_latency_seconds` - Histogram of inference request durations
- `goblin_docqa_inference_errors_total` - Counter of inference errors
- `goblin_docqa_inference_requests_total` - Counter of inference requests

### API Metrics

- `goblin_docqa_api_requests_total` - Counter of API requests by endpoint and method
- `goblin_docqa_rate_limit_hits_total` - Counter of rate limit violations

### Resource Metrics

- `goblin_docqa_memory_bytes` - Current memory usage in bytes
- `goblin_docqa_cpu_usage_percent` - Current CPU usage percentage

### Copilot Metrics

- `goblin_docqa_copilot_tokens_used_total` - Counter of Copilot API tokens used
- `goblin_docqa_copilot_errors_total` - Counter of Copilot API errors

## Alerting Rules

Prometheus alerting rules are defined in `prometheus/alerting_rules.yml`:

### Queue Overload

- **Alert**: `DocQAQueueOverload`
- **Condition**: Queue length > 8 for 30 seconds
- **Severity**: Warning

### High Memory Usage

- **Alert**: `DocQAMemoryHigh`
- **Condition**: Memory usage > 512MB for 30 seconds
- **Severity**: Warning

### High Inference Error Rate

- **Alert**: `DocQAInferenceErrorsHigh`
- **Condition**: Error rate > 0.1 errors/second over 5 minutes
- **Severity**: Error

### High Rate Limit Hits

- **Alert**: `DocQARateLimitHigh`
- **Condition**: Rate limit hit rate > 0.5 hits/second over 5 minutes
- **Severity**: Warning

### Slow Inference Latency

- **Alert**: `DocQAInferenceLatencyHigh`
- **Condition**: 95th percentile latency > 30s over 5 minutes
- **Severity**: Warning

### High Copilot Token Usage

- **Alert**: `DocQACopilotUsageHigh`
- **Condition**: Token usage rate > 100,000 tokens/hour for 10 minutes
- **Severity**: Warning

## Setup

1. **Prometheus Configuration**:

   ```yaml
   scrape_configs:
     - job_name: 'goblin-docqa'
       static_configs:
         - targets: ['localhost:8000']
       metrics_path: '/metrics'
   ```

2. **Load Alerting Rules**:
   ```yaml

   rule_files:

     - 'prometheus/alerting_rules.yml'
   ```

3. **Alertmanager Configuration**:
   Configure Alertmanager to handle alerts based on severity levels.

## Monitoring Dashboard

Use Grafana with Prometheus datasource to create dashboards visualizing:

- Queue length over time
- Inference latency percentiles
- Error rates by type
- Resource usage trends
- Copilot token consumption

## Runbooks

Create runbooks for each alert type:

- `docs/runbooks/queue-overload.md` - Handling queue overload situations
- `docs/runbooks/high-memory.md` - Memory optimization and scaling
- `docs/runbooks/inference-errors.md` - Debugging inference failures
- `docs/runbooks/rate-limits.md` - Rate limit tuning and abuse handling
- `docs/runbooks/high-latency.md` - Performance optimization
- `docs/runbooks/copilot-usage.md` - Token usage monitoring and cost control
