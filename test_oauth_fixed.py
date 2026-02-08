#!/usr/bin/env python3
import os
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
            print("🔐 Authentication required...")
            print("   A browser window will open for Google OAuth approval")
            print("   Use redirect URI: http://localhost:8080")
            print("   Complete the authorization in your browser")
            input("   Press Enter to continue...")

            # Use local server flow with configured redirect URI
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES, redirect_uri="http://localhost:8080"
            )
            try:
                # Run local server on port 8080
                creds = flow.run_local_server(
                    port=8080, host="localhost", open_browser=True
                )
                print("✅ Authentication successful!")
            except Exception as e:
                print(f"❌ Local server flow failed: {e}")
                print("🔄 Trying alternative authentication method...")
                # Fallback to manual flow
                auth_url, _ = flow.authorization_url(prompt="consent")
                print(f"\n🔗 Please visit this URL to authorize: {auth_url}")
                print(
                    "   After authorization, you'll be redirected to http://localhost:8080"
                )
                print("   Copy the 'code' parameter from the URL and paste it here:")
                code = input("📋 Enter the authorization code: ").strip()
                flow.fetch_token(
                    code=code,
                    authorization_response=f"http://localhost:8080/?code={code}",
                )
                creds = flow.credentials

        with open(token_file, "w") as token:
            token.write(creds.to_json())

    service = build("drive", "v3", credentials=creds)

    # Test API call
    about = service.about().get(fields="user").execute()
    user_email = about.get("user", {}).get("emailAddress", "Unknown")

    print("✅ Google API connected successfully")
    print(f"   Authenticated as: {user_email}")

    # Test file upload
    file_metadata = {
        "name": "OAuth Test",
        "mimeType": "application/vnd.google-apps.document",
    }
    file = service.files().create(body=file_metadata, fields="id").execute()
    file_id = file.get("id")

    print(f"✅ Test file created: {file_id}")

    # Clean up test file
    service.files().delete(fileId=file_id).execute()
    print("✅ Test file cleaned up")

    return True


if __name__ == "__main__":
    import sys

    try:
        test_drive_api()
        print("\n🎉 OAuth setup completed successfully!")
    except Exception as e:
        print(f"❌ OAuth setup failed: {e}")
        sys.exit(1)
