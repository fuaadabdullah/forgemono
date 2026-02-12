#!/usr/bin/env python3
"""
Google OAuth Setup Helper for Raptor Mini Automation
Helps set up Google Drive API credentials for automated Colab deployment.
"""

import os
import json
import sys
import webbrowser


def check_credentials():
    """Check if credentials are properly set up"""
    print("🔍 Checking Google OAuth Setup...")

    creds_file = "credentials.json"
    token_file = "token.json"

    if os.path.exists(creds_file):
        print("✅ credentials.json found")
        try:
            with open(creds_file, "r") as f:
                creds_data = json.load(f)
            if "installed" in creds_data:
                print("✅ Valid OAuth client credentials detected")
            else:
                print("❌ Invalid credentials.json format")
                return False
        except json.JSONDecodeError:
            print("❌ credentials.json is not valid JSON")
            return False
    else:
        print("❌ credentials.json not found")
        return False

    if os.path.exists(token_file):
        print("✅ token.json found (authentication cached)")
    else:
        print("⚠️  token.json not found (first-time authentication required)")

    return True


def test_google_api():
    """Test Google API connectivity"""
    print("\n🔗 Testing Google API connection...")

    try:
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build
    except ImportError:
        print("❌ Google API libraries not installed")
        print("   Run: pip install -r requirements-automation.txt")
        return False

    try:
        SCOPES = ["https://www.googleapis.com/auth/drive.file"]
        creds = None

        token_file = "token.json"
        creds_file = "credentials.json"

        if os.path.exists(token_file):
            creds = Credentials.from_authorized_user_file(token_file, SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                print("🔐 Authentication required...")
                flow = InstalledAppFlow.from_client_secrets_file(creds_file, SCOPES)
                creds = flow.run_local_server(port=0)

            with open(token_file, "w") as token:
                token.write(creds.to_json())

        service = build("drive", "v3", credentials=creds)

        # Test API call - get user info
        about = service.about().get(fields="user").execute()
        user_email = about.get("user", {}).get("emailAddress", "Unknown")

        print("✅ Google API connected successfully")
        print(f"   Authenticated as: {user_email}")

        return True

    except Exception as e:
        print(f"❌ Google API test failed: {e}")
        return False


def open_google_console():
    """Open Google Cloud Console in browser"""
    console_url = "https://console.cloud.google.com/"
    print(f"🌐 Opening Google Cloud Console: {console_url}")
    webbrowser.open(console_url)


def create_credentials_template():
    """Create a template for credentials.json"""
    template = {
        "installed": {
            "client_id": "YOUR_CLIENT_ID_HERE",
            "project_id": "YOUR_PROJECT_ID_HERE",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_secret": "YOUR_CLIENT_SECRET_HERE",
            "redirect_uris": ["http://localhost"],
        }
    }

    if not os.path.exists("credentials.json"):
        with open("credentials.json", "w") as f:
            json.dump(template, f, indent=2)
        print("📝 Created credentials.json template")
        print("   ⚠️  Replace placeholder values with your actual OAuth credentials")
    else:
        print("⚠️  credentials.json already exists")


def show_setup_instructions():
    """Display setup instructions"""
    print("""
📋 Google OAuth Setup Instructions
=====================================

1. 🌐 Create Google Cloud Project:
   - Go to: https://console.cloud.google.com/
   - Create a new project or select existing one

2. 🔧 Enable APIs:
   - Search for "Google Drive API" and enable it
   - Search for "Google Colab API" and enable it (if available)

3. 🔐 Create OAuth Credentials:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth 2.0 Client IDs"
   - Choose "Desktop application"
   - Download the JSON file as "credentials.json"

4. 📁 Place credentials.json in this directory

5. 🧪 Test setup:
   python setup_google_oauth.py --test

6. 🚀 Run automation:
   python automate_raptor_colab.py

🔗 Useful Links:
- Google Cloud Console: https://console.cloud.google.com/
- Google Drive API Docs: https://developers.google.com/drive/api
- OAuth 2.0 Setup: https://developers.google.com/identity/protocols/oauth2

""")


def main():
    """Main setup function"""
    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "--check":
            success = check_credentials()
            if success:
                print("\n✅ Google OAuth setup looks good!")
            else:
                print("\n❌ Google OAuth setup incomplete")
                show_setup_instructions()

        elif command == "--test":
            if check_credentials():
                success = test_google_api()
                if success:
                    print("\n✅ Google API test successful!")
                else:
                    print("\n❌ Google API test failed")
            else:
                print("❌ Fix credentials setup first")

        elif command == "--console":
            open_google_console()

        elif command == "--template":
            create_credentials_template()

        elif command == "--help":
            show_setup_instructions()

        else:
            print(f"Unknown command: {command}")
            print("Available commands: --check, --test, --console, --template, --help")

    else:
        print("🛠️  Google OAuth Setup Helper")
        print("Usage: python setup_google_oauth.py [command]")
        print("")
        print("Commands:")
        print("  --check     Check if credentials are set up")
        print("  --test      Test Google API connectivity")
        print("  --console   Open Google Cloud Console in browser")
        print("  --template  Create credentials.json template")
        print("  --help      Show detailed setup instructions")
        print("")
        print("Example:")
        print("  python setup_google_oauth.py --check")


if __name__ == "__main__":
    main()
