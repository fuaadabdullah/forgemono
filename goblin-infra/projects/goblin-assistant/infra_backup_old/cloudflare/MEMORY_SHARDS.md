# Memory Shards for Goblins 🧠

Your edge goblins now have distributed memory using Cloudflare's storage primitives.

## ✅ Currently Active (KV)

### 1. **Rate Limit Buckets** 🪣
- **Key Pattern**: `ratelimit:{ip}`
- **Purpose**: Track request counts per IP
- **TTL**: 60 seconds
- **Usage**: Automatic, enforced on all requests

### 2. **User Session State** 🎫
- **Key Pattern**: `session:{token}`
- **Purpose**: Store active user sessions
- **TTL**: Custom per session
- **Data**: `{ user_id, expires_at, last_activity }`

### 3. **Conversation Context** 💬
- **Key Pattern**: `conversation:{user_id}`
- **Purpose**: Cache last 10 messages (non-sensitive)
- **TTL**: 1 hour
- **Data**: `{ messages: [{ timestamp, preview }], last_updated }`

### 4. **Feature Flags** 🚩
- **Key Pattern**: `feature_flags`
- **Purpose**: Dynamic feature enablement
- **TTL**: 5 minutes
- **Data**: `{ api_enabled, rate_limiting_enabled, new_ui_enabled, ... }`

### 5. **Response Caching** 💾
- **Key Pattern**: `cache:{pathname}{search}`
- **Purpose**: Cache GET responses for common endpoints
- **TTL**: 5 minutes
- **Endpoints**: `/health`, `/models`, `/providers`, `/settings`

### 6. **Analytics Events** 📊
- **Key Pattern**: `analytics:{timestamp}:{ip}`
- **Purpose**: Store request logs
- **TTL**: 24 hours
- **Data**: `{ timestamp, ip, method, path, event_type, duration_ms }`

### 7. **Security Events** 🔒
- **Key Pattern**: `security:{timestamp}:{ip}`
- **Purpose**: Log blocked requests and security incidents
- **TTL**: 7 days
- **Data**: `{ timestamp, ip, event_type, reason }`

## 🔮 Advanced Options (Optional)

### D1 (SQLite at the Edge)
For structured, queryable data:
- User preferences
- Audit logs
- API usage tracking
- Feature flag management

**Setup**:
```bash
wrangler d1 create goblin-assistant-db
wrangler d1 execute goblin-assistant-db --file=./schema.sql
```

Then uncomment the D1 binding in `wrangler.toml`.

### Durable Objects
For stateful, real-time features:
- WebSocket chat rooms
- Multi-user collaboration
- Precise rate limiting
- Real-time presence

**File**: `durable-object.js` (implementation ready)

## 📈 Storage Usage

- **KV**: Free tier = 100,000 reads/day, 1,000 writes/day
- **D1**: Free tier = 5 million reads/month, 100,000 writes/month
- **Durable Objects**: $0.15 per million requests

## 🎯 Current Implementation

All KV shards are active and working. Your backend now has:
- ✅ Fast session validation (no DB hit)
- ✅ Conversation context caching (reduced DB load)
- ✅ Feature flags (instant rollouts)
- ✅ Rate limiting (no backend processing)
- ✅ Response caching (instant responses)

**Worker Size**: 10.74 KB (still tiny!)
**Active Since**: December 2, 2025
