#!/usr/bin/env python3
"""
Final OAuth Fix Guide
Complete step-by-step instructions to fix OAuth redirect URI issue
"""


def show_final_guide():
    print("""
🎯 FINAL OAUTH FIX - Step by Step
==================================

The OAuth authentication is failing because Google Cloud Console doesn't allow the redirect URI.

REQUIRED ACTION: Add redirect URI to Google Cloud Console

📋 Exact Steps:
===============

1. 🌐 Open: https://console.cloud.google.com/apis/credentials
2. 📱 Find your OAuth client: "AI Documentation System" or similar
3. 🖱️  Click on it to edit
4. 🔧 In "Authorized redirect URIs" section:
   - Click "ADD URI"
   - Enter: http://localhost:8080
   - Click "SAVE"

That's it! One URI addition fixes everything.

✅ After adding the URI:
=======================

Run this command:
    python test_oauth_fixed.py

Expected result:
- Browser opens for OAuth approval
- You approve the permissions
- Script completes successfully
- token.json is created

🎉 Then run the full automation:
    python automate_raptor_colab.py

The automation will:
- Upload notebook to Google Drive
- Provide Colab link
- Set up ngrok tunnel
- Update your .env file

🚨 IMPORTANT:
=============

- Add EXACTLY: http://localhost:8080
- No trailing slash variations
- Click "SAVE" after adding
- Then run the OAuth test immediately

This is the final step - OAuth will work perfectly after this! 🎉
""")


if __name__ == "__main__":
    show_final_guide()
