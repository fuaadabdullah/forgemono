#!/usr/bin/env python3
import os
import sys
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/drive.file"]


def test_drive_api():
    creds = None
    token_file = "token.json"

    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            print("🔐 Google OAuth Authentication Required")
            print("=" * 50)
            print("Complete these steps:")
            print("1. Visit the authorization URL below")
            print("2. Grant permission for Google Drive access")
            print("3. Copy the authorization code from the resulting URL")
            print("4. Paste the code when prompted")
            print("=" * 50)

            input("Press Enter to continue...")

            # Create OAuth flow with out-of-band redirect URI
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES, redirect_uri="urn:ietf:wg:oauth:2.0:oob"
            )

            # Get authorization URL
            auth_url, _ = flow.authorization_url(prompt="consent")
            print("\n🔗 Authorization URL:")
            print(f"{auth_url}")
            print(
                "\nAfter granting permission, you'll see an authorization code on the page."
            )
            print("Copy that code and paste it below.")

            code = input("📋 Enter the authorization code: ").strip()

            if not code:
                print("❌ No authorization code provided")
                return False

            try:
                print("🔄 Exchanging code for tokens...")
                # Exchange code for tokens
                flow.fetch_token(code=code)
                creds = flow.credentials
                print("✅ Authentication successful!")
            except Exception as e:
                print(f"❌ Token exchange failed: {e}")
                return False

        # Save credentials
        with open(token_file, "w") as token:
            token.write(creds.to_json())
        print(f"💾 Credentials saved to {token_file}")

    # Test the API
    print("\n🧪 Testing Google Drive API...")
    service = build("drive", "v3", credentials=creds)

    # Test API call
    about = service.about().get(fields="user").execute()
    user_email = about.get("user", {}).get("emailAddress", "Unknown")

    print("✅ Google API connected successfully")
    print(f"   Authenticated as: {user_email}")

    # Test file upload
    print("\n📤 Testing file upload...")
    file_metadata = {
        "name": "OAuth Test - " + str(os.getpid()),
        "mimeType": "application/vnd.google-apps.document",
    }
    file = service.files().create(body=file_metadata, fields="id").execute()
    file_id = file.get("id")

    print(f"✅ Test file created: {file_id}")

    # Clean up test file
    service.files().delete(fileId=file_id).execute()
    print("🧹 Test file cleaned up")

    return True


if __name__ == "__main__":
    try:
        success = test_drive_api()
        if success:
            print("\n🎉 OAuth setup completed successfully!")
            print("You can now run the main automation script.")
        else:
            print("\n❌ OAuth setup failed.")
            sys.exit(1)
    except Exception as e:
        print(f"❌ OAuth setup failed: {e}")
        sys.exit(1)
