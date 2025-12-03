# R2 Quick Reference

## 🚀 Deploy R2 Infrastructure

```bash
cd /Users/fuaadabdullah/ForgeMonorepo/apps/goblin-assistant/infra/cloudflare

# Create all R2 buckets
chmod +x setup_r2_buckets.sh
./setup_r2_buckets.sh

# Configure CORS for audio bucket
wrangler r2 bucket cors put goblin-audio --config cors_config.json

# Deploy worker with R2 bindings
wrangler deploy
```

## 📦 R2 Buckets

| Bucket | Purpose | Size | Monthly Cost |
|--------|---------|------|--------------|
| `goblin-audio` | TTS audio, voice recordings | 100GB | $1.50 |
| `goblin-logs` | Application logs | 50GB | $0.75 |
| `goblin-uploads` | User-uploaded files | 500GB | $7.50 |
| `goblin-training` | Model training artifacts | 2TB | $30.00 |
| `goblin-cache` | LLM response cache | 200GB | $3.00 |

**Total:** $42.75/month (vs $322/month S3 = **86% savings**)

## 💻 Common Operations

### List Buckets
```bash
wrangler r2 bucket list
```

### Upload File
```bash
wrangler r2 object put goblin-audio/test.mp3 --file ./test.mp3
```

### Download File
```bash
wrangler r2 object get goblin-audio/test.mp3 --file ./downloaded.mp3
```

### Delete File
```bash
wrangler r2 object delete goblin-audio/test.mp3
```

### List Objects
```bash
wrangler r2 object list goblin-audio --prefix tts/
```

## 🔧 Worker Integration

```javascript
import { R2Storage } from './r2_helper.js';

export default {
  async fetch(request, env) {
    const storage = new R2Storage(env);

    // Upload audio
    await storage.uploadAudio('tts/response.mp3', audioBuffer, {
      userId: 'user123',
      source: 'elevenlabs'
    });

    // Get audio URL
    const url = await storage.getAudioUrl('tts/response.mp3');

    // Upload user file
    await storage.uploadUserFile('user123', 'doc.pdf', fileBuffer);

    // Cache LLM response
    await storage.cacheResponse('prompt:abc', llmResponse, 604800);

    // Get stats
    const stats = await storage.getStats();

    return new Response('OK');
  }
}
```

## 📊 Monitor Usage

```bash
# View R2 analytics
open "https://dash.cloudflare.com/${CF_ACCOUNT_ID}/r2/overview"
```

## 🎯 Files Created

- `r2_buckets.json` - Bucket configuration
- `r2_helper.js` - Storage utilities
- `setup_r2_buckets.sh` - Deployment script
- `cors_config.json` - CORS rules
- `R2_GUIDE.md` - Complete documentation
- `R2_QUICK_REF.md` - This file

## 💰 Cost Savings vs S3

- **Storage:** $42.75 vs $65.55 = $22.80 saved
- **Egress:** $0 vs $256.50 = $256.50 saved
- **Total:** $42.75 vs $322.05 = **$279.30/month saved (86%)**
- **Annual:** **$3,351.60 saved**

## 🔗 Links

- [R2 Documentation](https://developers.cloudflare.com/r2/)
- [R2 Pricing](https://developers.cloudflare.com/r2/pricing/)
- [Wrangler R2 Commands](https://developers.cloudflare.com/workers/wrangler/commands/#r2)
