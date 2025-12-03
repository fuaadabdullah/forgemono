# Enable Analytics Engine

## ⚠️ Analytics Engine Not Enabled

Error: **"You need to enable Analytics Engine"**

## 🚀 How to Enable

### Step 1: Open Analytics Engine Dashboard

```bash
open "https://dash.cloudflare.com/a9c52e892f7361bab3bfd084c6ffaccb/workers/analytics-engine"
```

### Step 2: Enable Analytics Engine

1. Click **"Enable Analytics Engine"** or **"Get Started"**
2. Review terms and click **"Enable"**
3. No payment method needed (totally free for 10M data points/month!)

### Step 3: Uncomment Analytics Binding

```bash
cd /Users/fuaadabdullah/ForgeMonorepo/apps/goblin-assistant/infra/cloudflare

# Edit wrangler.toml and uncomment Analytics Engine section:
# [[analytics_engine_datasets]]
# binding = "GOBLIN_ANALYTICS"
```

Or just run:
```bash
# Replace commented lines with active binding
sed -i '' 's/# \[\[analytics_engine_datasets\]\]/[[analytics_engine_datasets]]/' wrangler.toml
sed -i '' 's/# binding = "GOBLIN_ANALYTICS"/binding = "GOBLIN_ANALYTICS"/' wrangler.toml
```

### Step 4: Deploy with Analytics

```bash
./deploy.sh
```

---

## 💰 Analytics Engine Pricing

| Resource | Free Tier | Cost |
|----------|-----------|------|
| Data points | 10M/month | $0 |
| Storage | Unlimited (90 day retention) | $0 |
| Queries | Unlimited | $0 |
| Overage | 1M data points | $0.25 |

**Estimated for Goblin Assistant:** $0/month (well under 10M data points)

---

## ✅ Current Status

- ✅ Analytics helper code created (`cloudflare_analytics.js`)
- ✅ SQL queries ready (`CLOUDFLARE_ANALYTICS_GUIDE.md`)
- ✅ Documentation complete
- ❌ Analytics Engine not enabled yet
- ❌ Binding commented out in `wrangler.toml`

---

## 🚀 After Enabling

1. **Uncomment binding** in `wrangler.toml`
2. **Deploy:** `./deploy.sh`
3. **View analytics:** Dashboard or SQL queries
4. **Save $50-200/month** vs Datadog!

---

**Ready?** Click the link above to enable Analytics Engine! 🚀
