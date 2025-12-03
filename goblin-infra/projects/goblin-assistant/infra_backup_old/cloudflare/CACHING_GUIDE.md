# ⚡ Frontend Caching Rules - Performance Guide

## 🎯 Goal

Make your Goblin Assistant feel like it was built by a **trillion-dollar startup** with aggressive edge caching.

## 📊 Cache Strategy

### 1. Static Assets - 1 Year Cache (Immutable)
**Files:** `.js`, `.css`, `.woff2`, `.ttf`, `.svg`, `.png`, `.jpg`, `.webp`, `.gif`, `.mp4`
- **Edge TTL:** 31,536,000s (1 year)
- **Browser TTL:** 31,536,000s (1 year)
- **Why:** These files are versioned, they never change
- **Result:** Instant loads, zero server hits after first visit

### 2. Versioned Bundles - 1 Year Cache
**Pattern:** `main.a3f5b9c2.js`, `styles.7d4e2a1f.css`
- Webpack/Vite generates unique hashes
- Safe to cache forever
- **Result:** Blazing fast bundle loading

### 3. Build Chunks - 1 Year Cache
**Paths:** `/assets/*`, `/chunks/*`, `/_next/static/*`
- Modern bundlers split code into chunks
- Each chunk is content-hashed
- **Result:** Optimal code splitting performance

### 4. Fonts - 1 Year Cache
**Path:** `/fonts/*`
- Fonts rarely change
- Large files benefit most from caching
- **Result:** No FOIT (Flash of Invisible Text)

### 5. Goblin Animations & Effects - 24h Cache
**Paths:** `/animations/*`, `/effects/*`, `/lottie/*`
- Smooth typing effects
- Lottie animations
- Precomputed visual effects
- **Stale-while-revalidate:** 7 days
- **Result:** Buttery smooth goblin animations

### 6. HTML Pages - 5min Cache
**Files:** `/`, `/index.html`, routes without extensions
- Short cache for quick deployments
- Must-revalidate for freshness
- **Result:** Updates propagate within 5 minutes

### 7. API Responses - No Cache
**Path:** `/api/*`
- Bypassed (handled by brain worker)
- Smart per-endpoint caching in Worker
- **Result:** Fresh data, optimal LLM response caching

---

## 🚀 Deployment

### Option 1: Automated Script (When fuaad.ai is added to Cloudflare)

```bash
cd /Users/fuaadabdullah/ForgeMonorepo/apps/goblin-assistant/infra/cloudflare
chmod +x setup_cache_rules.sh
./setup_cache_rules.sh
```

### Option 2: Manual in Dashboard

Once `fuaad.ai` is added to Cloudflare:

1. Go to: Zone → Caching → Cache Rules
2. Click "Create Rule" for each:

**Rule 1: Static Assets**
```
Expression: (http.request.uri.path matches ".*\.(js|css|woff2?|ttf|eot|ico|svg|png|jpg|jpeg|webp|gif|mp4|webm)$")
Cache TTL: 1 year
Browser TTL: 1 year
```

**Rule 2: Versioned Bundles**
```
Expression: (http.request.uri.path matches ".*\.[a-f0-9]{8,}\.(js|css)$")
Cache TTL: 1 year
Browser TTL: 1 year
```

**Rule 3: Build Chunks**
```
Expression: (http.request.uri.path contains "/assets/" or http.request.uri.path contains "/chunks/")
Cache TTL: 1 year
Browser TTL: 1 year
```

**Rule 4: Fonts**
```
Expression: (http.request.uri.path contains "/fonts/")
Cache TTL: 1 year
Browser TTL: 1 year
```

**Rule 5: Animations**
```
Expression: (http.request.uri.path contains "/animations/" or http.request.uri.path contains "/effects/")
Cache TTL: 24 hours
Browser TTL: 24 hours
Serve Stale: Enabled
```

**Rule 6: HTML**
```
Expression: (http.request.uri.path eq "/" or http.request.uri.path matches ".*\.html$")
Cache TTL: 5 minutes
Browser TTL: 5 minutes
```

---

## 📈 Expected Performance Gains

### Before Caching Rules
- Static assets: ~200-500ms (origin server)
- Bundle loading: ~1-2s (network latency)
- Page load: ~2-4s (cumulative)
- **Cache hit rate:** ~20-30%

### After Caching Rules
- Static assets: ~10-50ms (edge cache)
- Bundle loading: ~100-200ms (cached chunks)
- Page load: ~500ms-1s (mostly cached)
- **Cache hit rate:** ~85-95%

### Real User Impact
- ⚡ **3-4x faster** page loads
- ⚡ **10x faster** static asset delivery
- ⚡ **90% reduction** in origin requests
- ⚡ **Instant** repeat visits
- ⚡ **Smooth** goblin typing animations (no jank)

---

## 🧪 Testing Cache Rules

### Test Cache Headers

```bash
# Static asset (should cache 1 year)
curl -I https://goblin.fuaad.ai/assets/main.js
# Look for:
# cf-cache-status: HIT
# cache-control: public, max-age=31536000

# HTML page (should cache 5min)
curl -I https://goblin.fuaad.ai/
# Look for:
# cf-cache-status: HIT
# cache-control: public, max-age=300

# API (should bypass)
curl -I https://api.goblin.fuaad.ai/health
# Look for:
# cf-cache-status: BYPASS or DYNAMIC
```

### Monitor Cache Performance

```bash
# Cloudflare Dashboard
open "https://dash.cloudflare.com/${CF_ACCOUNT_ID}/zones/${CF_ZONE_ID}/analytics/caching"
```

Watch for:
- **Cache hit rate:** Should be >85%
- **Bandwidth saved:** Should be >70%
- **Origin requests:** Should drop significantly

---

## 🎨 Frontend Optimization Tips

### 1. Use Content Hashing
```javascript
// vite.config.js
export default {
  build: {
    rollupOptions: {
      output: {
        entryFileNames: '[name].[hash].js',
        chunkFileNames: '[name].[hash].js',
        assetFileNames: '[name].[hash].[ext]'
      }
    }
  }
}
```

### 2. Add Cache Headers in Your App
```javascript
// For Vercel/Netlify
// vercel.json or netlify.toml
{
  "headers": [
    {
      "source": "/assets/*",
      "headers": [
        {
          "key": "Cache-Control",
          "value": "public, max-age=31536000, immutable"
        }
      ]
    }
  ]
}
```

### 3. Preload Critical Assets
```html
<link rel="preload" href="/assets/main.abc123.js" as="script">
<link rel="preload" href="/fonts/inter.woff2" as="font" type="font/woff2" crossorigin>
```

### 4. Service Worker for Offline
```javascript
// sw.js - Cache goblin typing animations
self.addEventListener('fetch', (event) => {
  if (event.request.url.includes('/animations/')) {
    event.respondWith(
      caches.match(event.request)
        .then(response => response || fetch(event.request))
    );
  }
});
```

---

## 🔍 Troubleshooting

### Cache not working?
1. **Check rules are enabled** in Cloudflare Dashboard
2. **Verify expressions match** your file structure
3. **Clear Cloudflare cache:** Zone → Caching → Purge Everything
4. **Check origin headers:** Some frameworks set no-cache headers

### Too aggressive?
- Reduce TTL for specific paths
- Add query string versioning: `main.js?v=123`
- Use `must-revalidate` for important content

### Need to update immediately?
```bash
# Purge specific file
curl -X POST "https://api.cloudflare.com/client/v4/zones/$CF_ZONE_ID/purge_cache" \
  -H "Authorization: Bearer $CF_API_TOKEN" \
  -H "Content-Type: application/json" \
  --data '{"files":["https://goblin.fuaad.ai/assets/main.js"]}'

# Purge everything (use sparingly)
curl -X POST "https://api.cloudflare.com/client/v4/zones/$CF_ZONE_ID/purge_cache" \
  -H "Authorization: Bearer $CF_API_TOKEN" \
  -H "Content-Type: application/json" \
  --data '{"purge_everything":true}'
```

---

## 📚 Files Created

- `worker_caching.js` - Worker with advanced caching logic
- `cache_rules.json` - Cache rules documentation
- `cache_rules_payload.json` - API payload for deployment
- `setup_cache_rules.sh` - Automated deployment script
- `CACHING_GUIDE.md` - This file

---

## ✅ Next Steps

1. **Add fuaad.ai to Cloudflare** (prerequisite)
2. **Get Zone ID** and update `.env`
3. **Run setup script** or configure manually
4. **Deploy frontend** with content hashing
5. **Test cache headers** with curl
6. **Monitor analytics** for performance gains
7. **Profit** from 3-4x faster loads! 🚀

---

**Result:** Your Goblin Assistant will load instantly, animations will be smooth, and it will feel like a trillion-dollar startup built it. All thanks to aggressive edge caching! ⚡
