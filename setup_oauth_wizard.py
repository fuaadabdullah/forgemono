#!/usr/bin/env python3
"""
Complete Google OAuth Setup Wizard for Raptor Mini Automation
Guides users through the entire Google Cloud Console setup process.
"""

import os
import json
import webbrowser
import subprocess
import sys


def print_header():
    """Print the setup wizard header"""
    print("""
🎯 Google OAuth Setup Wizard for Raptor Mini
==============================================

This wizard will guide you through setting up Google OAuth credentials
for automated Colab deployment. Follow each step carefully.

Prerequisites:
- Google account
- Internet connection
- Web browser

Let's get started!
""")


def step_1_create_project():
    """Step 1: Create Google Cloud Project"""
    print("""
📋 Step 1: Select/Create Google Cloud Project
===============================================

You provided project information for "AI Documentation System":
- Project Name: AI Documentation System
- Project ID: ai-documentation-system
- Project Number: 62628447432

If this project doesn't exist yet, create it. If it exists, select it.

1. Open Google Cloud Console in your browser
2. If prompted, sign in with your Google account
3. Select "AI Documentation System" from the project dropdown
   OR create a new project with this name if it doesn't exist

Note: Make sure you're using the correct project for Raptor Mini automation.
""")

    # Use the specific project URL
    project_url = (
        "https://console.cloud.google.com/welcome?project=ai-documentation-system"
    )
    print(f"🌐 Opening project: {project_url}")

    try:
        webbrowser.open(project_url)
        print("✅ Browser opened successfully")
    except Exception as e:
        print(f"❌ Could not open browser: {e}")
        print(f"Please manually visit: {project_url}")

    input(
        "\nPress Enter when you've selected/created the 'AI Documentation System' project..."
    )


def step_2_enable_apis():
    """Step 2: Enable required APIs"""
    print("""
📋 Step 2: Enable Google Drive API
====================================

1. In Google Cloud Console, go to "APIs & Services" > "Library"
2. Search for "Google Drive API"
3. Click on "Google Drive API"
4. Click "Enable"

Note: This enables programmatic access to Google Drive.
""")

    api_url = "https://console.cloud.google.com/apis/library/drive.googleapis.com?project=ai-documentation-system"
    print(
        f"🌐 Opening Google Drive API page for project 'ai-documentation-system': {api_url}"
    )

    try:
        webbrowser.open(api_url)
        print("✅ Browser opened successfully")
    except Exception as e:
        print(f"❌ Could not open browser: {e}")
        print(f"Please manually visit: {api_url}")

    input("\nPress Enter when you've enabled the Google Drive API...")


def step_3_create_credentials():
    """Step 3: Create OAuth credentials"""
    print("""
📋 Step 3: Create OAuth 2.0 Credentials
=========================================

1. In Google Cloud Console, go to "APIs & Services" > "Credentials"
2. Click "+ CREATE CREDENTIALS"
3. Select "OAuth 2.0 Client IDs"
4. Choose "Desktop application" as the application type
5. Enter a name (e.g., "Raptor Mini Desktop Client")
6. Click "Create"
7. In the popup, click "Download JSON"
8. Save the file as "credentials.json" in this directory

⚠️  IMPORTANT: Download the JSON file immediately - you can only download it once!
""")

    creds_url = "https://console.cloud.google.com/apis/credentials?project=ai-documentation-system"
    print(
        f"🌐 Opening credentials page for project 'ai-documentation-system': {creds_url}"
    )

    try:
        webbrowser.open(creds_url)
        print("✅ Browser opened successfully")
    except Exception as e:
        print(f"❌ Could not open browser: {e}")
        print(f"Please manually visit: {creds_url}")

    input("\nPress Enter after downloading credentials.json...")


def step_4_verify_setup():
    """Step 4: Verify the setup"""
    print("""
📋 Step 4: Verify Setup
========================

Let's check if everything is configured correctly...
""")

    # Check if credentials.json exists
    if not os.path.exists("credentials.json"):
        print("❌ credentials.json not found in current directory")
        print(f"   Current directory: {os.getcwd()}")
        return False

    # Check if credentials.json has real values
    try:
        with open("credentials.json", "r") as f:
            creds_data = json.load(f)

        if "installed" not in creds_data:
            print("❌ Invalid credentials.json format")
            return False

        installed = creds_data["installed"]

        # Check for placeholder values
        client_id = installed.get("client_id", "")
        client_secret = installed.get("client_secret", "")

        if (
            "YOUR_CLIENT_ID_HERE" in client_id
            or "YOUR_CLIENT_SECRET_HERE" in client_secret
        ):
            print("❌ credentials.json still contains placeholder values")
            print("   Please replace with your actual OAuth credentials")
            return False

        print("✅ credentials.json looks valid")

    except json.JSONDecodeError:
        print("❌ credentials.json is not valid JSON")
        return False

    # Test Google API connection
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
        if os.path.exists(token_file):
            creds = Credentials.from_authorized_user_file(token_file, SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                print("🔐 First-time authentication required...")
                print("   A browser window will open for Google OAuth approval")
                input("   Press Enter to continue...")

                flow = InstalledAppFlow.from_client_secrets_file(
                    "credentials.json", SCOPES
                )
                creds = flow.run_local_server(port=0)

            with open(token_file, "w") as token:
                token.write(creds.to_json())

        service = build("drive", "v3", credentials=creds)

        # Test API call
        about = service.about().get(fields="user").execute()
        user_email = about.get("user", {}).get("emailAddress", "Unknown")

        print("✅ Google API connected successfully")
        print(f"   Authenticated as: {user_email}")

        return True

    except Exception as e:
        print(f"❌ Google API test failed: {e}")
        return False


def step_5_test_automation():
    """Step 5: Test the full automation"""
    print("""
📋 Step 5: Test Full Automation
================================

Let's run the complete Raptor Mini automation to make sure everything works!
""")

    test_script = "test_oauth_setup.py"
    test_content = '''
#!/usr/bin/env python3
"""Test OAuth setup by attempting a small Drive API call"""

import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/drive.file']

def test_drive_api():
    creds = None
    token_file = 'token.json'

    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)

        with open(token_file, 'w') as token:
            token.write(creds.to_json())

    service = build('drive', 'v3', credentials=creds)

    # Create a test folder
    file_metadata = {
        'name': 'Raptor Mini Test',
        'mimeType': 'application/vnd.google-apps.folder'
    }

    file = service.files().create(body=file_metadata, fields='id').execute()
    folder_id = file.get('id')

    print(f"✅ Test folder created: {folder_id}")

    # Clean up test folder
    service.files().delete(fileId=folder_id).execute()
    print("✅ Test folder cleaned up")

    return True

if __name__ == "__main__":
    try:
        test_drive_api()
        print("🎉 OAuth setup test PASSED!")
    except Exception as e:
        print(f"❌ OAuth setup test FAILED: {e}")
        exit(1)
'''

    with open(test_script, "w") as f:
        f.write(test_content)

    print("🧪 Running OAuth setup test...")
    result = subprocess.run(
        [sys.executable, test_script], capture_output=True, text=True
    )

    if result.returncode == 0:
        print("✅ OAuth setup test PASSED!")
        print(result.stdout)
    else:
        print("❌ OAuth setup test FAILED!")
        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)

    # Clean up test script
    if os.path.exists(test_script):
        os.remove(test_script)


def main():
    """Main setup wizard"""
    print_header()

    try:
        step_1_create_project()
        step_2_enable_apis()
        step_3_create_credentials()

        if step_4_verify_setup():
            print("""
🎉 OAuth Setup Complete!
=========================

Your Google OAuth credentials are properly configured. You can now run:

    python automate_raptor_colab.py

This will:
1. Authenticate with Google (first time only)
2. Upload notebook to Google Drive
3. Provide Colab link for manual execution
4. Set up ngrok tunneling
5. Update your .env file

Happy automating! 🚀
""")
        else:
            print("""
❌ Setup Verification Failed
==============================

Please check the errors above and try again. Common issues:

1. credentials.json not downloaded or corrupted
2. Wrong application type (must be "Desktop application")
3. Google Drive API not enabled
4. Network connectivity issues

Run this wizard again: python setup_oauth_wizard.py
""")

    except KeyboardInterrupt:
        print("\n\n⚠️  Setup cancelled by user")
        print("You can resume by running: python setup_oauth_wizard.py")

    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        print("Please try again or check the troubleshooting guide")


if __name__ == "__main__":
    main()
