#!/usr/bin/env python3
"""
Update OAuth client redirect URIs using Google APIs
"""

import json
import sys
import subprocess
import requests


def update_oauth_redirect_uris():
    # Load credentials
    with open("credentials.json", "r") as f:
        creds_data = json.load(f)

    client_id = creds_data["installed"]["client_id"]
    project_id = creds_data["installed"]["project_id"]

    print(f"Client ID: {client_id}")
    print(f"Project ID: {project_id}")

    # Try to use gcloud auth to get credentials
    result = subprocess.run(
        ["gcloud", "auth", "print-access-token"], capture_output=True, text=True
    )

    if result.returncode != 0:
        print("Failed to get access token from gcloud")
        return False

    access_token = result.stdout.strip()

    # Use the access token to make API calls
    # Get the OAuth client details
    url = f"https://oauth2.googleapis.com/v2/clients/{client_id}"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    response = requests.get(url, headers=headers, timeout=30)
    print(f"GET response: {response.status_code}")
    print(f"Response: {response.text}")

    if response.status_code == 200:
        client_data = response.json()
        print("Current redirect URIs:", client_data.get("redirectUris", []))

        # Update redirect URIs
        update_data = {
            "redirectUris": [
                "http://localhost",
                "http://localhost:8080",
                "http://localhost:3000",
                "urn:ietf:wg:oauth:2.0:oob",
            ]
        }

        update_response = requests.patch(
            url, headers=headers, json=update_data, timeout=30
        )
        print(f"PATCH response: {update_response.status_code}")
        print(f"Update response: {update_response.text}")

        return update_response.status_code == 200
    else:
        print("Failed to get OAuth client details")
        return False


if __name__ == "__main__":
    success = update_oauth_redirect_uris()
    sys.exit(0 if success else 1)
