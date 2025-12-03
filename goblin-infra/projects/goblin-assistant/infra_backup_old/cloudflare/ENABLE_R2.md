# Enable R2 in Cloudflare Dashboard

## ⚠️ R2 Not Enabled Yet

The R2 API returned error code 10042: **"Please enable R2 through the Cloudflare Dashboard."**

## 🚀 How to Enable R2

### Step 1: Open R2 Dashboard

```bash
open "https://dash.cloudflare.com/a9c52e892f7361bab3bfd084c6ffaccb/r2/overview"
```

### Step 2: Enable R2

1. Click **"Enable R2"** or **"Get Started"**
2. Accept the R2 terms of service
3. Add payment method (if not already added)
   - R2 has a **free tier**: 10GB storage + 1 million Class A operations
   - Only charged above free tier
4. Click **"Enable R2"**

### Step 3: Run Setup Script

Once R2 is enabled:

```bash
cd /Users/fuaadabdullah/ForgeMonorepo/apps/goblin-assistant/infra/cloudflare
./setup_r2_buckets.sh
```

### Step 4: Verify Buckets

```bash
wrangler r2 bucket list
```

Should show:
- goblin-audio
- goblin-logs
- goblin-uploads
- goblin-training
- goblin-cache
- (+ preview versions)

---

## 💰 R2 Free Tier

| Resource | Free Tier | Overage Cost |
|----------|-----------|--------------|
| Storage | 10 GB | $0.015/GB |
| Class A (writes) | 1 million/month | $4.50/million |
| Class B (reads) | 10 million/month | $0.36/million |
| **Egress** | **Unlimited** | **$0.00 forever** |

**Why this matters:**
- S3 charges $0.09/GB for egress = $90/TB
- R2 egress is FREE = **$90/TB savings**
- For 10TB downloads/month: **$900/month saved**

---

## 🔗 Next Steps After Enabling

1. ✅ Enable R2 in Dashboard (this step)
2. ✅ Run `./setup_r2_buckets.sh` to create buckets
3. ✅ Deploy worker with R2 bindings: `wrangler deploy`
4. ✅ Configure public access for audio bucket (if needed)
5. ✅ Test R2 access in worker code
6. ✅ Start uploading files and saving money!

---

## 📚 Documentation

- [Cloudflare R2 Docs](https://developers.cloudflare.com/r2/)
- [R2 Pricing](https://developers.cloudflare.com/r2/pricing/)
- [R2 API Reference](https://developers.cloudflare.com/api/operations/r2-create-bucket)

---

**Ready?** Open the dashboard and click "Enable R2"! 🚀
