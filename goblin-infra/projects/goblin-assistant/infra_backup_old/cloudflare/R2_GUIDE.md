# ⚡ R2 Storage Setup - 86% Cheaper Than S3

## 🎯 Why R2?

Cloudflare R2 saves you **$98/month per TB** compared to AWS S3 by offering:
- ✅ **Free egress** (S3 charges $90/TB!)
- ✅ **35% cheaper storage** ($0.015/GB vs $0.023/GB)
- ✅ **S3-compatible API** (drop-in replacement)
- ✅ **Global edge access** (fast from anywhere)
- ✅ **No bandwidth fees** (unlimited downloads)

---

## 💰 Cost Comparison

### AWS S3 (Traditional)
- Storage: **$0.023/GB/month** = $23/TB
- PUT requests: **$5.00 per million**
- GET requests: **$0.40 per million**
- **Egress: $0.09/GB** = $90/TB 🚨
- **Monthly cost (1TB + downloads): $113+**

### Cloudflare R2 (Modern)
- Storage: **$0.015/GB/month** = $15/TB
- Class A (writes): **$4.50 per million**
- Class B (reads): **$0.36 per million**
- **Egress: $0.00** ✨
- **Monthly cost (1TB + downloads): $15**

### 💵 Savings Per TB
- Storage: **$8/month**
- Egress: **$90/month**
- **Total: $98/month (86% cheaper!)**

For 10TB: **$980/month savings** 🤯

---

## 🪣 R2 Buckets for Goblin Assistant

### 1. `goblin-audio` (100GB estimated)
**Purpose:** Audio files (TTS output, voice recordings, sound effects)

**Why R2?**
- Audio files are large (1-10MB each)
- Frequently streamed to users
- S3 egress would cost **$9/TB** → R2 saves **$900/100GB**

**Lifecycle:**
- Auto-delete after 90 days
- Transition to infrequent access after 30 days

**Usage:**
```javascript
await storage.uploadAudio('tts/response_123.mp3', audioBuffer);
const url = await storage.getAudioUrl('tts/response_123.mp3');
```

**Cost:** ~$1.50/month (vs $11/month S3)

---

### 2. `goblin-logs` (50GB estimated)
**Purpose:** Application logs, error traces, audit logs

**Why R2?**
- Logs are write-heavy, rarely read
- Only accessed during debugging
- S3 storage + occasional downloads → expensive

**Lifecycle:**
- Auto-delete after 30 days
- Compressed on upload

**Usage:**
```javascript
await storage.uploadLog('error/2024-12-02/app_123.log', logData);
```

**Cost:** ~$0.75/month (vs $8/month S3)

---

### 3. `goblin-uploads` (500GB estimated)
**Purpose:** User-uploaded reference files, documents, images

**Why R2?**
- Users frequently re-download their files
- S3 egress charges = death by 1000 cuts
- R2 = unlimited free downloads

**Max file size:** 50MB per file

**Usage:**
```javascript
await storage.uploadUserFile('user123', 'reference.pdf', fileBuffer);
const files = await storage.listUserFiles('user123');
await storage.deleteUserFile(fileKey);
```

**Cost:** ~$7.50/month (vs $56/month S3)

---

### 4. `goblin-training` (2TB estimated)
**Purpose:** Model training artifacts, fine-tuning datasets, embeddings

**Why R2?**
- Training artifacts are HUGE (100MB-10GB each)
- Downloaded during model deployment
- S3 egress = **$180/TB** for downloads

**Lifecycle:**
- Keep for 180 days (6 months)
- Transition to infrequent access after 60 days

**Usage:**
```javascript
await storage.uploadTrainingArtifact('fine-tuning/model_v1.safetensors', data);
```

**Cost:** ~$30/month (vs $226/month S3)

---

### 5. `goblin-cache` (200GB estimated)
**Purpose:** LLM response cache (overflow from KV)

**Why R2?**
- KV is limited to 25MB values
- R2 can store unlimited JSON responses
- Frequently accessed → free egress matters

**Lifecycle:**
- Auto-delete after 7 days
- Short TTL, high churn

**Usage:**
```javascript
await storage.cacheResponse('prompt:abc123', llmResponse, 604800);
const cached = await storage.getCachedResponse('prompt:abc123');
```

**Cost:** ~$3/month (vs $21/month S3)

---

## 📊 Total Monthly Costs

### R2 (Goblin Assistant)
| Bucket | Size | Cost |
|--------|------|------|
| goblin-audio | 100GB | $1.50 |
| goblin-logs | 50GB | $0.75 |
| goblin-uploads | 500GB | $7.50 |
| goblin-training | 2TB | $30.00 |
| goblin-cache | 200GB | $3.00 |
| **Total** | **2.85TB** | **$42.75** |

### S3 (Equivalent)
| Bucket | Size | Storage | Egress | Total |
|--------|------|---------|--------|-------|
| audio | 100GB | $2.30 | $9.00 | $11.30 |
| logs | 50GB | $1.15 | $4.50 | $5.65 |
| uploads | 500GB | $11.50 | $45.00 | $56.50 |
| training | 2TB | $46.00 | $180.00 | $226.00 |
| cache | 200GB | $4.60 | $18.00 | $22.60 |
| **Total** | **2.85TB** | **$65.55** | **$256.50** | **$322.05** |

### 💰 Monthly Savings: $279.30 (86%)
### 💰 Annual Savings: $3,351.60

---

## 🚀 Deployment

### Step 1: Create R2 Buckets

```bash
cd /Users/fuaadabdullah/ForgeMonorepo/apps/goblin-assistant/infra/cloudflare
chmod +x setup_r2_buckets.sh
./setup_r2_buckets.sh
```

This creates:
- 5 production buckets
- 5 preview buckets (for staging)

### Step 2: Configure CORS (Audio Bucket)

```bash
wrangler r2 bucket cors put goblin-audio --config cors_config.json
```

### Step 3: Deploy Worker with R2 Bindings

```bash
wrangler deploy
```

Worker now has access to all R2 buckets via bindings:
- `env.GOBLIN_AUDIO`
- `env.GOBLIN_LOGS`
- `env.GOBLIN_UPLOADS`
- `env.GOBLIN_TRAINING`
- `env.GOBLIN_CACHE_R2`

### Step 4: Test R2 Access

```javascript
import { R2Storage } from './r2_helper.js';

export default {
  async fetch(request, env) {
    const storage = new R2Storage(env);

    // Upload test file
    await storage.uploadAudio('test.mp3', new Uint8Array([1,2,3]));

    // Get stats
    const stats = await storage.getStats();
    return new Response(JSON.stringify(stats, null, 2));
  }
}
```

### Step 5: Configure Public Access (Audio)

For audio streaming, make `goblin-audio` bucket public:

1. Go to: Cloudflare Dashboard → R2 → `goblin-audio`
2. Settings → Public Access → **Enable**
3. Copy public URL: `https://pub-<id>.r2.dev`
4. (Optional) Add custom domain: `audio.goblin.fuaad.ai`

---

## 🔧 Advanced Features

### Lifecycle Rules

```bash
# Auto-delete old logs after 30 days
wrangler r2 bucket lifecycle put goblin-logs \
  --rule '{"id":"delete-old-logs","expiration":{"days":30}}'

# Archive training artifacts to infrequent access
wrangler r2 bucket lifecycle put goblin-training \
  --rule '{"id":"archive-old","transition":{"days":60,"storage_class":"INFREQUENT_ACCESS"}}'
```

### Presigned URLs (Temporary Access)

```javascript
// Generate temporary upload URL for users
const presignedUrl = await env.GOBLIN_UPLOADS.createPresignedUrl(
  `users/${userId}/file.pdf`,
  { expiresIn: 3600 } // 1 hour
);
```

### Multipart Uploads (Large Files)

```javascript
// Upload 1GB+ files in chunks
const upload = await env.GOBLIN_TRAINING.createMultipartUpload('model.safetensors');
// Upload parts...
await upload.complete();
```

---

## 📈 Monitoring

### Dashboard Metrics

```bash
# View R2 analytics
open "https://dash.cloudflare.com/${CF_ACCOUNT_ID}/r2/overview"
```

Watch for:
- **Storage used** (GB)
- **Class A operations** (writes)
- **Class B operations** (reads)
- **Egress** (always $0!)

### Worker Stats

```javascript
// Get storage stats via Worker
const storage = new R2Storage(env);
const stats = await storage.getStats();

// Returns:
// [
//   { bucket: 'audio', objects: 1234, size: '50.2 GB' },
//   { bucket: 'logs', objects: 5678, size: '12.8 GB' },
//   ...
// ]
```

---

## 🎨 Integration Examples

### TTS Audio Pipeline

```javascript
// 1. Generate TTS audio
const audio = await elevenLabs.textToSpeech('Hello, Goblin!');

// 2. Upload to R2
const key = `tts/${Date.now()}_hello.mp3`;
await storage.uploadAudio(key, audio, {
  userId: 'user123',
  source: 'elevenlabs',
  text: 'Hello, Goblin!'
});

// 3. Return streaming URL
const url = await storage.getAudioUrl(key);
return new Response(JSON.stringify({ audioUrl: url }));
```

### User File Upload

```javascript
// 1. Receive file from user
const formData = await request.formData();
const file = formData.get('file');

// 2. Upload to R2
await storage.uploadUserFile(
  userId,
  file.name,
  await file.arrayBuffer(),
  { contentType: file.type, fileSize: file.size }
);

// 3. List user files
const files = await storage.listUserFiles(userId);
return new Response(JSON.stringify(files));
```

### LLM Response Caching

```javascript
// 1. Check cache first
const cacheKey = `prompt:${hash(prompt)}`;
let response = await storage.getCachedResponse(cacheKey);

if (!response) {
  // 2. Cache miss, call LLM
  response = await callLLM(prompt);

  // 3. Cache for 7 days
  await storage.cacheResponse(cacheKey, response, 604800);
}

return new Response(JSON.stringify(response));
```

---

## 🔍 Troubleshooting

### Permission Denied
- Check wrangler.toml has correct bucket bindings
- Verify API token has R2 permissions
- Ensure bucket exists: `wrangler r2 bucket list`

### CORS Errors
- Configure CORS: `wrangler r2 bucket cors put <bucket> --config cors_config.json`
- Check allowed origins match your frontend URL

### Large File Uploads
- Use multipart upload for files >100MB
- Consider streaming uploads with `ReadableStream`

### Public Access Not Working
- Enable public access in Dashboard
- Configure custom domain for vanity URLs
- Verify DNS CNAME points to R2 public URL

---

## ✅ Checklist

- [x] Created `r2_buckets.json` (bucket configuration)
- [x] Updated `wrangler.toml` (R2 bindings)
- [x] Created `r2_helper.js` (storage utilities)
- [x] Created `setup_r2_buckets.sh` (deployment script)
- [x] Created `cors_config.json` (CORS rules)
- [ ] Run `./setup_r2_buckets.sh` to create buckets
- [ ] Deploy worker: `wrangler deploy`
- [ ] Test R2 access in worker code
- [ ] Configure public access for audio bucket
- [ ] Monitor storage usage in Dashboard

---

**Result:** You now have **86% cheaper storage** than S3, with **unlimited free egress**. Upload audio files, logs, user uploads, and training artifacts without worrying about bandwidth costs. Your Goblin Assistant infrastructure just got way more affordable! 💰⚡
