#!/usr/bin/env python3
"""
Alternative OAuth Setup - Use Pre-configured Redirect URI
This script uses a fixed redirect URI that matches Google Cloud Console config
"""

import os
import json
import webbrowser
import subprocess
import sys


def create_alternative_oauth_flow():
    """Create an alternative OAuth flow that uses the configured redirect URI"""

    print("""
🔄 Alternative OAuth Setup
===========================

Since we can't modify Google Cloud Console via CLI, let's use a different approach:

1. Use a fixed redirect URI that matches your Google Cloud Console config
2. This bypasses the random port issue

Current config allows: http://localhost
We'll use: http://localhost:8080 (or another fixed port)
""")

    # Create a modified OAuth test script
    oauth_test_script = """#!/usr/bin/env python3
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
            print("🔐 Authentication required...")
            print("   A browser window will open for Google OAuth approval")
            print("   Use redirect URI: http://localhost:8080")
            input("   Press Enter to continue...")

            # Use fixed redirect URI instead of random port
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json',
                SCOPES,
                redirect_uri='http://localhost:8080'
            )
            # Run local server on fixed port
            creds = flow.run_local_server(port=8080, host='localhost')

        with open(token_file, 'w') as token:
            token.write(creds.to_json())

    service = build('drive', 'v3', credentials=creds)

    # Test API call
    about = service.about().get(fields="user").execute()
    user_email = about.get('user', {}).get('emailAddress', 'Unknown')

    print(f"✅ Google API connected successfully")
    print(f"   Authenticated as: {user_email}")

    # Test file upload
    file_metadata = {'name': 'OAuth Test', 'mimeType': 'application/vnd.google-apps.document'}
    file = service.files().create(body=file_metadata, fields='id').execute()
    file_id = file.get('id')

    print(f"✅ Test file created: {file_id}")

    # Clean up test file
    service.files().delete(fileId=file_id).execute()
    print("✅ Test file cleaned up")

    return True

if __name__ == "__main__":
    try:
        test_drive_api()
        print("\\n🎉 OAuth setup completed successfully!")
    except Exception as e:
        print(f"❌ OAuth setup failed: {e}")
        exit(1)
"""

    with open("test_oauth_fixed.py", "w") as f:
        f.write(oauth_test_script)

    print("✅ Created alternative OAuth test script: test_oauth_fixed.py")

    print("""
📋 Next Steps:
==============

1. Run the fixed OAuth test:
   python test_oauth_fixed.py

2. This will:
   - Use fixed redirect URI: http://localhost:8080
   - Open browser for OAuth approval
   - Create token.json for future use

3. After successful authentication, run:
   python automate_raptor_colab.py

⚠️  Note: This approach uses a fixed port (8080) that should work with your current
   Google Cloud Console OAuth configuration.
""")


def run_fixed_oauth_test():
    """Run the fixed OAuth test"""
    if not os.path.exists("test_oauth_fixed.py"):
        create_alternative_oauth_flow()

    print("🚀 Running fixed OAuth test...")
    result = subprocess.run(
        [sys.executable, "test_oauth_fixed.py"], capture_output=True, text=True
    )

    if result.returncode == 0:
        print("✅ OAuth test PASSED!")
        print(result.stdout)
        return True
    else:
        print("❌ OAuth test FAILED!")
        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)
        return False


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--run":
        run_fixed_oauth_test()
    else:
        create_alternative_oauth_flow()
