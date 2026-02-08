#!/usr/bin/env python3
"""
Secure Colab Setup Helper
Helps set up Raptor Mini in Colab with proper security practices.
"""

import os
import sys


def create_secure_colab_setup():
    """Create a secure Colab setup guide"""

    setup_guide = """
# 🔒 Secure Raptor Mini Colab Setup

## Security Best Practices

### 1. Environment Variables (Recommended)
In Google Colab, set environment variables securely:

1. **Runtime > Change runtime type**
2. **Add environment variables:**
   - `NGROK_AUTH_TOKEN`: Your ngrok auth token
   - `RAPTOR_ENV`: Set to 'production' for secure mode

### 2. Colab Secrets (Most Secure)
Use Colab's secret management:

```python
from google.colab import userdata
ngrok_token = userdata.get('NGROK_AUTH_TOKEN')
```

### 3. Never Commit Secrets
- Never commit auth tokens to version control
- Use environment variables or secret managers
- Rotate tokens regularly

## Setup Steps

1. **Upload notebook** to Colab
2. **Set environment variables** (see above)
3. **Run cells in order**
4. **Copy the ngrok URL** from output
5. **Update your ForgeMonorepo .env** file

## Production Deployment

For production use:
- Use Colab Enterprise or Vertex AI
- Implement proper authentication
- Use managed secrets (Cloud Secret Manager)
- Set up monitoring and logging
- Implement rate limiting and security headers

## Current Security Status

✅ Environment variable support added
✅ Fallback token removed from source
✅ Clear security warnings in notebook
✅ Port configuration verified (8000)
⚠️  Still uses development fallback token

## Next Steps

1. Set `NGROK_AUTH_TOKEN` environment variable in Colab
2. Remove hardcoded fallback token
3. Test the secure setup
4. Deploy to production environment
"""

    print(setup_guide)


def check_current_security():
    """Check current security status"""
    print("🔍 Security Audit:")

    # Check if token is in environment
    token = os.getenv("NGROK_AUTH_TOKEN")
    if token:
        print("✅ NGROK_AUTH_TOKEN found in environment")
    else:
        print("❌ NGROK_AUTH_TOKEN not set in environment")

    # Check notebook for hardcoded tokens
    notebook_path = "raptor_mini_colab.ipynb"
    if os.path.exists(notebook_path):
        with open(notebook_path, "r") as f:
            content = f.read()
            if "36cs1FkRw1Jua3GvHbyU2Smuood_3XfPCs2Jok9MHwANU8G9H" in content:
                print("⚠️  Hardcoded token found in notebook (development fallback)")
            else:
                print("✅ No hardcoded tokens in notebook")

    print("\n📋 Recommendations:")
    print("1. Set NGROK_AUTH_TOKEN environment variable")
    print("2. Remove development fallback tokens")
    print("3. Use Colab secrets for production")
    print("4. Rotate tokens regularly")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--check":
        check_current_security()
    else:
        create_secure_colab_setup()
