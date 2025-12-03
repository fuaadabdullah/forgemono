# Cloudflare Analytics - Free Observability

## 🎯 Why Cloudflare Analytics?

You're already using **Datadog** for observability, but Cloudflare Analytics gives you **free** complementary insights:

- ✅ **Latency insights** - p50, p95, p99 by endpoint
- ✅ **Error maps** - Status codes, error rates, failure patterns
- ✅ **Geographic heatmaps** - Where users are, datacenter performance
- ✅ **Cache hit ratios** - KV cache performance, R2 cache effectiveness
- ✅ **LLM performance** - Provider latency, token usage, model comparison

**Cost:** $0 (vs Datadog's $15/host/month+)

---

## 📊 What Gets Tracked

### 1. Request Latency
- Total request time (edge → origin → response)
- P50, P95, P99 percentiles
- By endpoint, by provider, by geography

### 2. Error Rates
- HTTP status codes (4xx, 5xx)
- Error types and messages
- Error geographic distribution
- Endpoint-specific failure rates

### 3. Geographic Distribution
- User country, city, region
- Cloudflare datacenter (colo)
- Latency by geography
- Request volume heatmaps

### 4. Cache Performance
- Cache hit ratio (KV, R2, edge cache)
- Cache lookup time
- Most cached endpoints
- Cache effectiveness over time

### 5. LLM Performance
- Provider latency (Groq, OpenAI, Anthropic, local)
- Model performance comparison
- Token usage per request
- Cached vs fresh inference

---

## 🚀 Usage in Worker

### Automatic Tracking (Recommended)

```javascript
import { withAnalytics } from './cloudflare_analytics.js';

export default {
  async fetch(request, env, ctx) {
    return withAnalytics(request, env, ctx, async (analytics) => {
      // Your handler code
      const response = await handleRequest(request, env);

      // Track with metadata
      await analytics.trackRequest(response, {
        endpoint: '/api/chat',
        provider: 'groq',
        model: 'llama-3.1-8b',
        cacheStatus: 'hit',
        tokensUsed: 150,
        llmLatency: 245
      });

      return response;
    });
  }
}
```

### Manual Tracking

```javascript
import { CloudflareAnalytics } from './cloudflare_analytics.js';

export default {
  async fetch(request, env, ctx) {
    const analytics = new CloudflareAnalytics(env, request);

    try {
      const response = await handleRequest(request);

      // Track success
      await analytics.trackRequest(response, {
        endpoint: '/api/inference',
        provider: 'groq',
        model: 'llama-3.1-70b'
      });

      return response;
    } catch (error) {
      // Track error
      await analytics.trackError(error, {
        endpoint: '/api/inference',
        statusCode: 500,
        provider: 'groq'
      });

      throw error;
    }
  }
}
```

### Track Cache Performance

```javascript
const cacheStart = Date.now();
const cached = await env.GOBLIN_CACHE.get(cacheKey);
const cacheLookupTime = Date.now() - cacheStart;

await analytics.trackCache(cacheKey, !!cached, cacheLookupTime);
```

### Track LLM Inference

```javascript
const inferenceStart = Date.now();
const llmResponse = await callLLM(prompt);
const inferenceLatency = Date.now() - inferenceStart;

await analytics.trackLLMInference({
  provider: 'groq',
  model: 'llama-3.1-8b',
  latency: inferenceLatency,
  tokensUsed: llmResponse.usage.total_tokens,
  cached: false
});
```

---

## 📈 Viewing Analytics

### Cloudflare Dashboard

```bash
# Open Analytics Dashboard
open "https://dash.cloudflare.com/a9c52e892f7361bab3bfd084c6ffaccb/workers/analytics-engine"
```

**Available Views:**
- **Overview** - Request volume, latency, errors
- **Geographic** - World map with request heatmap
- **Status Codes** - 2xx, 4xx, 5xx breakdown
- **Custom Queries** - SQL queries for deep analysis

### SQL Queries (GraphQL API)

```bash
# Example: Query average latency by endpoint
curl -X POST "https://api.cloudflare.com/client/v4/accounts/a9c52e892f7361bab3bfd084c6ffaccb/analytics_engine/sql" \
  -H "Authorization: Bearer $CF_API_TOKEN_WORKERS" \
  -H "Content-Type: application/json" \
  --data '{
    "query": "SELECT index1 as endpoint, AVG(double1) as avg_latency FROM GOBLIN_ANALYTICS WHERE timestamp > NOW() - INTERVAL '\''24'\'' HOUR GROUP BY endpoint"
  }'
```

---

## 📊 Pre-Built Queries

### 1. Latency by Endpoint (Last 24h)

```sql
SELECT
  index1 as endpoint,
  AVG(double1) as avg_latency_ms,
  QUANTILE(double1, 0.95) as p95_latency_ms,
  QUANTILE(double1, 0.99) as p99_latency_ms,
  COUNT(*) as requests
FROM GOBLIN_ANALYTICS
WHERE timestamp > NOW() - INTERVAL '24' HOUR
GROUP BY endpoint
ORDER BY requests DESC
```

### 2. Error Rate by Endpoint

```sql
SELECT
  index1 as endpoint,
  SUM(CASE WHEN double2 >= 400 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as error_rate,
  COUNT(*) as total_requests,
  SUM(CASE WHEN double2 >= 500 THEN 1 ELSE 0 END) as server_errors
FROM GOBLIN_ANALYTICS
WHERE timestamp > NOW() - INTERVAL '1' HOUR
GROUP BY endpoint
```

### 3. Geographic Distribution

```sql
SELECT
  blob3 as country,
  COUNT(*) as requests,
  AVG(double1) as avg_latency_ms
FROM GOBLIN_ANALYTICS
WHERE timestamp > NOW() - INTERVAL '24' HOUR
GROUP BY country
ORDER BY requests DESC
LIMIT 20
```

### 4. Cache Hit Ratio

```sql
SELECT
  index1 as endpoint,
  SUM(double5) * 100.0 / COUNT(*) as cache_hit_rate,
  COUNT(*) as total_requests,
  SUM(double5) as cache_hits
FROM GOBLIN_ANALYTICS
WHERE timestamp > NOW() - INTERVAL '1' HOUR
  AND index1 != 'error'
GROUP BY endpoint
```

### 5. LLM Provider Performance

```sql
SELECT
  index2 as provider,
  index3 as model,
  AVG(double3) as avg_llm_latency_ms,
  QUANTILE(double3, 0.95) as p95_llm_latency_ms,
  SUM(double4) as total_tokens,
  COUNT(*) as requests
FROM GOBLIN_ANALYTICS
WHERE timestamp > NOW() - INTERVAL '24' HOUR
  AND index1 = 'llm-inference'
GROUP BY provider, model
ORDER BY requests DESC
```

---

## 🔄 Datadog Integration (Optional)

Send Cloudflare Analytics to Datadog for unified observability:

```javascript
// Export analytics to Datadog
async function exportToDatadog(analytics, datadogApiKey) {
  const metrics = {
    series: [
      {
        metric: 'goblin.latency',
        points: [[Date.now() / 1000, analytics.latency]],
        type: 'gauge',
        tags: [
          `endpoint:${analytics.endpoint}`,
          `provider:${analytics.provider}`,
          `country:${analytics.country}`
        ]
      }
    ]
  };

  await fetch('https://api.datadoghq.com/api/v1/series', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'DD-API-KEY': datadogApiKey
    },
    body: JSON.stringify(metrics)
  });
}
```

---

## 📊 Data Schema

### Blobs (Strings)
- `blob[0]` - Latency string (for sorting)
- `blob[1]` - Cloudflare datacenter (colo)
- `blob[2]` - User country
- `blob[3]` - User city
- `blob[4]` - Endpoint
- `blob[5]` - LLM provider
- `blob[6]` - LLM model
- `blob[7]` - Cache status

### Doubles (Numbers)
- `double[0]` - Latency (ms)
- `double[1]` - HTTP status code
- `double[2]` - LLM latency (ms)
- `double[3]` - Tokens used
- `double[4]` - Cache hit (1) or miss (0)

### Indexes (Grouping)
- `index[0]` - Status code or event type
- `index[1]` - Endpoint
- `index[2]` - LLM provider
- `index[3]` - Country

---

## 💰 Cost Comparison

### Datadog (Current)
- **Host-based:** $15/host/month (minimum)
- **Custom metrics:** $0.05/metric/month
- **Log ingestion:** $0.10/GB
- **APM:** $31/host/month
- **Estimated:** $50-200/month for Goblin Assistant

### Cloudflare Analytics (Free!)
- **Data points:** 10M/month free (then $0.25 per 1M)
- **Storage:** Unlimited (retained for 90 days)
- **Queries:** Unlimited
- **Geographic data:** Included
- **Estimated:** $0/month (well under 10M data points)

**Savings:** $50-200/month 💰

---

## 🎯 Use Cases

### 1. Latency Monitoring (Fallback for Datadog)
If Datadog goes down, Cloudflare Analytics still tracks:
- Request latency by endpoint
- Geographic latency variations
- LLM provider performance

### 2. Cost Optimization
- Identify slow endpoints → optimize
- Compare LLM provider latency → choose fastest
- Track cache hit ratio → improve caching strategy

### 3. Geographic Insights
- Where are users? → deploy closer datacenters
- Which colos are slow? → route around
- Regional error rates → investigate

### 4. Cache Effectiveness
- Low cache hit rate? → improve cache keys
- High cache latency? → optimize KV access
- Which endpoints benefit most from caching?

### 5. LLM Performance Tracking
- Which provider is fastest? (Groq, OpenAI, local)
- Which model is most efficient?
- Token usage patterns → cost optimization

---

## ✅ Deployment

Already configured! Just deploy:

```bash
cd /Users/fuaadabdullah/ForgeMonorepo/apps/goblin-assistant/infra/cloudflare
./deploy.sh
```

Worker now writes to `GOBLIN_ANALYTICS` automatically.

---

## 🔗 Resources

- [Analytics Engine Docs](https://developers.cloudflare.com/analytics/analytics-engine/)
- [SQL API Reference](https://developers.cloudflare.com/analytics/analytics-engine/sql-api/)
- [GraphQL API](https://developers.cloudflare.com/analytics/graphql-api/)
- [Dashboard](https://dash.cloudflare.com/a9c52e892f7361bab3bfd084c6ffaccb/workers/analytics-engine)

---

**Result:** Free observability with latency insights, error maps, geographic heatmaps, and cache analytics. Perfect fallback for Datadog! 📊⚡
