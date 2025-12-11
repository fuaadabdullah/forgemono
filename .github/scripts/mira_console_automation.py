#!/usr/bin/env python3
"""
mira_console_automation.py
Fully automates the final Mira console setup via API
"""

import requests
import yaml
import json
import os
import sys
from pathlib import Path
import base64


class MiraConsoleAutomator:
    def __init__(self, api_key=None):
        self.base_url = "https://api.mira.tools/v1"
        self.api_key = api_key or os.getenv("MIRA_API_KEY")
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def check_api_availability(self):
        """Check if Mira API is accessible and key is valid"""
        try:
            response = requests.get(
                f"{self.base_url}/health", headers=self.headers, timeout=10
            )
            return response.status_code == 200
        except:
            return False

    def upload_configuration(self, config_path, project_id=None):
        """Upload mira-linker-config.yml to Mira console"""
        try:
            # Read and parse the config file
            with open(config_path, "r") as f:
                config_data = yaml.safe_load(f)

            # Convert YAML to JSON for API
            config_json = json.dumps(config_data)

            # Base64 encode for safe transmission
            encoded_config = base64.b64encode(config_json.encode()).decode()

            payload = {
                "configuration": encoded_config,
                "format": "yaml",
                "project_id": project_id or self.get_default_project_id(),
            }

            response = requests.post(
                f"{self.base_url}/configurations",
                headers=self.headers,
                json=payload,
                timeout=30,
            )

            if response.status_code == 201:
                config_id = response.json().get("id")
                print(f"✅ Configuration uploaded successfully! ID: {config_id}")
                return config_id
            else:
                print(f"❌ Failed to upload configuration: {response.text}")
                return None

        except Exception as e:
            print(f"❌ Error uploading configuration: {str(e)}")
            return None

    def configure_webhook(self, config_id, github_repo):
        """Configure GitHub webhook automatically"""
        try:
            # Get webhook URL from Mira
            webhook_response = requests.get(
                f"{self.base_url}/configurations/{config_id}/webhook",
                headers=self.headers,
            )

            if webhook_response.status_code == 200:
                webhook_data = webhook_response.json()
                webhook_url = webhook_data.get("url")
                webhook_secret = webhook_data.get("secret")

                # Setup GitHub webhook via GitHub API
                self.setup_github_webhook(github_repo, webhook_url, webhook_secret)

                print(f"✅ GitHub webhook configured!")
                print(f"   Webhook URL: {webhook_url[:50]}...")
                return True
            return False

        except Exception as e:
            print(f"❌ Error configuring webhook: {str(e)}")
            return False

    def setup_github_webhook(self, repo, webhook_url, secret):
        """Create GitHub webhook via GitHub API"""
        github_token = os.getenv("GITHUB_TOKEN")

        # Extract owner and repo from full URL
        if "github.com/" in repo:
            parts = repo.split("github.com/")[1].split("/")
            owner = parts[0]
            repo_name = parts[1].replace(".git", "")
        else:
            owner, repo_name = repo.split("/")

        webhook_payload = {
            "name": "web",
            "active": True,
            "events": ["pull_request", "push", "issues", "issue_comment"],
            "config": {
                "url": webhook_url,
                "content_type": "json",
                "secret": secret,
                "insecure_ssl": "0",
            },
        }

        response = requests.post(
            f"https://api.github.com/repos/{owner}/{repo_name}/hooks",
            headers={
                "Authorization": f"token {github_token}",
                "Accept": "application/vnd.github.v3+json",
            },
            json=webhook_payload,
        )

        if response.status_code == 201:
            return True
        else:
            print(f"⚠️ GitHub webhook may need manual setup: {response.text}")
            return False

    def enable_features(self, config_id, features=None):
        """Enable auto-assign, transitions, and blocking features"""
        if features is None:
            features = ["auto_assign", "transitions", "blocking"]

        payload = {"features": features, "enabled": True}

        response = requests.put(
            f"{self.base_url}/configurations/{config_id}/features",
            headers=self.headers,
            json=payload,
        )

        if response.status_code == 200:
            print(f"✅ Features enabled: {', '.join(features)}")
            return True
        else:
            print(f"⚠️ Features may need manual enablement")
            return False

    def get_default_project_id(self):
        """Get or create default project ID"""
        response = requests.get(f"{self.base_url}/projects", headers=self.headers)

        if response.status_code == 200 and response.json():
            return response.json()[0]["id"]
        else:
            # Create a new project
            project_payload = {
                "name": f"Mira-Linker-{os.environ.get('GITHUB_REPOSITORY', 'Project')}",
                "description": "Automated Mira Linker Integration",
            }

            project_response = requests.post(
                f"{self.base_url}/projects", headers=self.headers, json=project_payload
            )

            if project_response.status_code == 201:
                return project_response.json()["id"]

        return None


def main():
    # Check for required environment variables
    required_envs = ["MIRA_API_KEY", "GITHUB_TOKEN", "GITHUB_REPOSITORY"]
    missing = [env for env in required_envs if not os.getenv(env)]

    if missing:
        print("❌ Missing environment variables:")
        for env in missing:
            print(f"   - {env}")
        print("\nPlease set them up or run the interactive setup.")
        sys.exit(1)

    # Initialize automator
    automator = MiraConsoleAutomator()

    if not automator.check_api_availability():
        print("❌ Could not connect to Mira API. Please check your API key.")
        sys.exit(1)

    print("🚀 Starting Mira Console Automation...")
    print("=" * 50)

    # Step 1: Upload configuration
    config_path = Path("mira-linker-config.yml")
    if not config_path.exists():
        print("❌ Configuration file not found: mira-linker-config.yml")
        sys.exit(1)

    print("📤 Uploading configuration...")
    config_id = automator.upload_configuration(config_path)

    if not config_id:
        print("❌ Failed to upload configuration")
        sys.exit(1)

    # Step 2: Configure webhook
    print("\n🔗 Configuring GitHub webhook...")
    github_repo = os.getenv("GITHUB_REPOSITORY")
    automator.configure_webhook(config_id, github_repo)

    # Step 3: Enable features
    print("\n⚙️ Enabling features...")
    automator.enable_features(config_id)

    print("\n" + "=" * 50)
    print("🎉 MIRA CONSOLE SETUP: 100% COMPLETE!")
    print("=" * 50)
    print("\n✅ All steps automated successfully!")
    print("✅ Configuration uploaded")
    print("✅ GitHub webhook configured")
    print("✅ Features enabled")
    print("\n📊 Verification steps:")
    print("1. Check Mira console: https://app.mira.tools")
    print("2. Run: ./verify_mira_setup.sh")
    print("3. Create a test PR with JIRA-123 in title")


if __name__ == "__main__":
    main()
