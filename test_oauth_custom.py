#!/usr/bin/env python3
import os
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/drive.file"]


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """Custom HTTP handler to capture OAuth callback"""

    def do_GET(self):
        """Handle the OAuth callback"""
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()

        # Parse the authorization code from the URL
        query = parse_qs(urlparse(self.path).query)
        if "code" in query:
            self.server.auth_code = query["code"][0]
            response_html = """
            <html>
            <body>
            <h2>✅ Authorization Successful!</h2>
            <p>You can close this window and return to the terminal.</p>
            <p>The authorization code has been captured.</p>
            </body>
            </html>
            """
        else:
            self.server.auth_code = None
            response_html = """
            <html>
            <body>
            <h2>❌ Authorization Failed</h2>
            <p>No authorization code received.</p>
            </body>
            </html>
            """

        self.wfile.write(response_html.encode())
        # Shutdown the server after handling the callback
        self.server.shutdown()


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
            print("   Complete the authorization in your browser")
            input("   Press Enter to start the local server and open browser...")

            # Create OAuth flow with explicit redirect URI
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES, redirect_uri="http://localhost"
            )

            # Get authorization URL
            auth_url, _ = flow.authorization_url(prompt="consent")
            print(f"\n🔗 Opening browser for authorization: {auth_url}")

            # Open browser
            import webbrowser

            webbrowser.open(auth_url)

            # Start local server to capture callback
            print(
                "📡 Starting local server on http://localhost:80 to capture authorization..."
            )
            server = HTTPServer(("localhost", 80), OAuthCallbackHandler)
            server.auth_code = None

            try:
                server.serve_forever()
            except KeyboardInterrupt:
                server.shutdown()

            if server.auth_code:
                print("✅ Authorization code received!")
                # Exchange code for tokens
                flow.fetch_token(code=server.auth_code)
                creds = flow.credentials
                print("✅ Tokens exchanged successfully!")
            else:
                print("❌ No authorization code received")
                return False

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
