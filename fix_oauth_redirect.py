#!/usr/bin/env python3
"""
Fix OAuth Redirect URI Configuration
Updates Google Cloud Console OAuth client with correct redirect URIs
"""

import json
import webbrowser
import os


def update_oauth_redirect_uri():
    """Guide user to update OAuth redirect URI in Google Cloud Console"""

    print("""
🔧 OAuth Redirect URI Fix
===========================

The OAuth flow is failing because the redirect URI doesn't match what's configured in Google Cloud Console.

Current issue:
- OAuth flow is trying to use: http://localhost:55992/
- Google Cloud Console only has: http://localhost

Solution: Add the specific redirect URI to your OAuth client configuration.

📋 Steps to Fix:
===============

1. Go to Google Cloud Console → APIs & Services → Credentials
2. Click on your OAuth 2.0 Client ID (Desktop application)
3. In the "Authorized redirect URIs" section, add:
   http://localhost:55992/
4. Click "Save"

Alternatively, for future-proofing, you can add:
   http://localhost
   http://localhost:*
   (This allows any port on localhost)

Let me open Google Cloud Console for you...
""")

    # Open Google Cloud Console credentials page
    creds_url = "https://console.cloud.google.com/apis/credentials"
    print(f"🌐 Opening: {creds_url}")

    try:
        webbrowser.open(creds_url)
        print("✅ Browser opened successfully")
    except Exception as e:
        print(f"❌ Could not open browser: {e}")
        print(f"Please manually visit: {creds_url}")

    print("""
⏳ After updating the redirect URI in Google Cloud Console:

1. Click "Save" in Google Cloud Console
2. Return to this terminal
3. Press Enter to continue
4. Run the OAuth test again

The OAuth authentication should work after this fix!
""")

    input("Press Enter after updating the redirect URI in Google Cloud Console...")

    print("""
🎯 Next Steps:
==============

Now run the OAuth test again:

    python setup_google_oauth.py --test

This should successfully authenticate and create a token.json file.
""")


if __name__ == "__main__":
    update_oauth_redirect_uri()
