#!/usr/bin/env python3
"""
Vercel Environment Variables Setup via REST API
Uses the Vercel REST API to set environment variables programmatically.
Much more reliable than the CLI for automation.
"""

import os
import sys
import subprocess
import json
import requests

# Environment variables to set
ENV_VARS = {
    "NEXT_PUBLIC_API_URL": "https://goblin-backend.fly.dev",
    "NEXT_PUBLIC_FASTAPI_URL": "https://goblin-backend.fly.dev",
    "NEXT_PUBLIC_DD_APPLICATION_ID": "goblin-assistant",
    "NEXT_PUBLIC_DD_ENV": "production",
    "NEXT_PUBLIC_DD_VERSION": "1.0.0",
}


def get_vercel_token():
    """Get Vercel token from CLI config"""
    try:
        # Try to read from Vercel CLI config
        config_path = os.path.expanduser("~/.config/vercel/auth.json")
        if os.path.exists(config_path):
            with open(config_path) as f:
                config = json.load(f)
                return config.get("token")

        # Fallback to environment variable
        return os.environ.get("VERCEL_TOKEN")
    except Exception as e:
        print(f"❌ Error getting Vercel token: {e}")
        return None


def get_project_id():
    """Get project ID from .vercel/project.json"""
    try:
        project_file = ".vercel/project.json"
        if os.path.exists(project_file):
            with open(project_file) as f:
                data = json.load(f)
                return data.get("projectId")
        return None
    except Exception as e:
        print(f"❌ Error reading project file: {e}")
        return None


def get_team_id():
    """Get team ID from .vercel/project.json"""
    try:
        project_file = ".vercel/project.json"
        if os.path.exists(project_file):
            with open(project_file) as f:
                data = json.load(f)
                return data.get("orgId")
        return None
    except Exception as e:
        return None


def set_env_var_api(token, project_id, team_id, key, value):
    """Set environment variable using Vercel API"""
    url = f"https://api.vercel.com/v10/projects/{project_id}/env"

    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    # Add team ID if present
    if team_id:
        url += f"?teamId={team_id}"

    payload = {
        "key": key,
        "value": value,
        "type": "encrypted",
        "target": ["production"],
    }

    try:
        response = requests.post(url, headers=headers, json=payload)

        if response.status_code == 200 or response.status_code == 201:
            print(f"✅ Set {key}")
            return True
        elif response.status_code == 409:
            # Variable already exists, try to update it
            print(f"⚠️  {key} already exists, attempting to update...")
            return update_env_var_api(token, project_id, team_id, key, value)
        else:
            print(f"❌ Failed to set {key}: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error setting {key}: {e}")
        return False


def get_env_vars_api(token, project_id, team_id):
    """Get all environment variables"""
    url = f"https://api.vercel.com/v9/projects/{project_id}/env"

    headers = {"Authorization": f"Bearer {token}"}

    if team_id:
        url += f"?teamId={team_id}"

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json().get("envs", [])
        return []
    except Exception as e:
        print(f"Warning: Could not fetch existing env vars: {e}")
        return []


def update_env_var_api(token, project_id, team_id, key, value):
    """Update existing environment variable"""
    # First, get the env var ID
    envs = get_env_vars_api(token, project_id, team_id)
    env_id = None

    for env in envs:
        if env.get("key") == key:
            env_id = env.get("id")
            break

    if not env_id:
        print(f"❌ Could not find {key} to update")
        return False

    url = f"https://api.vercel.com/v9/projects/{project_id}/env/{env_id}"

    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    if team_id:
        url += f"?teamId={team_id}"

    payload = {"value": value, "target": ["production"]}

    try:
        response = requests.patch(url, headers=headers, json=payload)

        if response.status_code == 200:
            print(f"✅ Updated {key}")
            return True
        else:
            print(f"❌ Failed to update {key}: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error updating {key}: {e}")
        return False


def main():
    print("🔧 Vercel Environment Variables Setup via API")
    print("=" * 60)

    # Get Vercel token
    token = get_vercel_token()
    if not token:
        print("❌ Vercel token not found!")
        print("   Run: vercel login")
        print("   Or set: export VERCEL_TOKEN=your_token")
        sys.exit(1)

    print("✅ Vercel token found")

    # Get project ID
    project_id = get_project_id()
    if not project_id:
        print("❌ Project not linked!")
        print("   Run: vercel link")
        sys.exit(1)

    print(f"✅ Project ID: {project_id}")

    # Get team ID (optional)
    team_id = get_team_id()
    if team_id:
        print(f"✅ Team ID: {team_id}")

    # Set environment variables
    print("\n📝 Setting environment variables...")
    success_count = 0

    for key, value in ENV_VARS.items():
        if set_env_var_api(token, project_id, team_id, key, value):
            success_count += 1

    print("\n" + "=" * 60)
    print(f"✅ Successfully set {success_count}/{len(ENV_VARS)} environment variables")

    if success_count == len(ENV_VARS):
        print("\n🚀 All environment variables configured!")
        print("   Next step: Deploy with 'vercel deploy --prod'")
        return 0
    else:
        print("\n⚠️  Some variables failed to set.")
        print("   Check the errors above and try again.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
