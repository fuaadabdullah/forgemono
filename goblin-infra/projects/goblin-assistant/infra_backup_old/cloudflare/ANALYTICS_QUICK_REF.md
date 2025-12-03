# Cloudflare Analytics - Quick Reference

## ✅ Setup Complete

- ✅ Analytics Engine binding added to `wrangler.toml`
- ✅ `CloudflareAnalytics` helper class created
- ✅ Pre-built SQL queries for common insights
- ✅ Ready to deploy

---

## 🚀 Deploy

```bash
cd /Users/fuaadabdullah/ForgeMonorepo/apps/goblin-assistant/infra/cloudflare
./deploy.sh
```

---

## 📊 View Analytics

### Dashboard
```bash
open "https://dash.cloudflare.com/a9c52e892f7361bab3bfd084c6ffaccb/workers/analytics-engine"
```

### SQL Query (via API)
```bash
curl -X POST "https://api.cloudflare.com/client/v4/accounts/a9c52e892f7361bab3bfd084c6ffaccb/analytics_engine/sql" \
  -H "Authorization: Bearer $CF_API_TOKEN_WORKERS" \
  -H "Content-Type: application/json" \
  --data '{"query": "SELECT * FROM GOBLIN_ANALYTICS LIMIT 10"}'
```

---

## 💻 Usage in Worker

### Quick Start
```javascript
import { CloudflareAnalytics } from './cloudflare_analytics.js';

export default {
  async fetch(request, env, ctx) {
    const analytics = new CloudflareAnalytics(env, request);

    try {
      const response = await handleRequest(request);

      await analytics.trackRequest(response, {
        endpoint: '/api/chat',
        provider: 'groq',
        model: 'llama-3.1-8b'
      });

      return response;
    } catch (error) {
      await analytics.trackError(error, { endpoint: '/api/chat' });
      throw error;
    }
  }
}
```

### Track Cache
```javascript
await analytics.trackCache(cacheKey, hit, lookupTime);
```

### Track LLM
```javascript
await analytics.trackLLMInference({
  provider: 'groq',
  model: 'llama-3.1-8b',
  latency: 245,
  tokensUsed: 150,
  cached: false
});
```

---

## 📈 Common Queries

### Latency by Endpoint
```sql
SELECT index1 as endpoint, AVG(double1) as avg_latency
FROM GOBLIN_ANALYTICS
WHERE timestamp > NOW() - INTERVAL '24' HOUR
GROUP BY endpoint
```

### Error Rate
```sql
SELECT
  SUM(CASE WHEN double2 >= 400 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as error_rate
FROM GOBLIN_ANALYTICS
WHERE timestamp > NOW() - INTERVAL '1' HOUR
```

### Cache Hit Ratio
```sql
SELECT
  SUM(double5) * 100.0 / COUNT(*) as cache_hit_rate
FROM GOBLIN_ANALYTICS
WHERE timestamp > NOW() - INTERVAL '1' HOUR
```

### Top Countries
```sql
SELECT blob3 as country, COUNT(*) as requests
FROM GOBLIN_ANALYTICS
WHERE timestamp > NOW() - INTERVAL '24' HOUR
GROUP BY country
ORDER BY requests DESC
LIMIT 10
```

---

## 💰 Cost

- **Free tier**: 10M data points/month
- **Overage**: $0.25 per 1M data points
- **Estimated**: $0/month (well under 10M)
- **Savings vs Datadog**: $50-200/month

---

## 📚 Files

- `cloudflare_analytics.js` - Helper class
- `CLOUDFLARE_ANALYTICS_GUIDE.md` - Complete guide
- `ANALYTICS_QUICK_REF.md` - This file

---

## 🔗 Dashboard Links

- [Analytics Engine](https://dash.cloudflare.com/a9c52e892f7361bab3bfd084c6ffaccb/workers/analytics-engine)
- [SQL API Docs](https://developers.cloudflare.com/analytics/analytics-engine/sql-api/)
- [GraphQL API](https://developers.cloudflare.com/analytics/graphql-api/)

---

**Result:** Free observability for latency, errors, geography, cache performance, and LLM metrics! 📊⚡
