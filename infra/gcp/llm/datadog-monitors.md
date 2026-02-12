# Datadog Monitors - LLM Canary

## p95 Latency

Query:
```
p95(last_10m):histogram_quantile(0.95, sum:ai.request_latency_seconds.bucket{service:llm-canary} by {le}) > 2
```
Suggested threshold: 2s (warning), 3s (critical).

## Model Loaded

Query:
```
min(last_5m):avg:ai.model_loaded{service:llm-canary} < 1
```
Suggested threshold: < 1 for 5m (critical).

## Memory Pressure

Query:
```
avg(last_10m):(avg:ai.memory_used_bytes{service:llm-canary} / avg:ai.memory_total_bytes{service:llm-canary}) > 0.9
```
Suggested threshold: 0.9 (warning), 0.95 (critical).

## Error Rate (optional)

Query:
```
100 * (sum:ai.request_errors_total{service:llm-canary}.as_count() / sum:ai.request_total{service:llm-canary}.as_count()) > 2
```
Suggested threshold: 2% (warning), 5% (critical).
