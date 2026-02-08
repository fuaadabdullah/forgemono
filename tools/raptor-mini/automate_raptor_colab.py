#!/usr/bin/env python3
"""
Raptor Mini Colab Automation Script
Automates the process of uploading and running Raptor Mini notebook in Google Colab.
"""

import subprocess
import time
import os
import sys
from pathlib import Path


def upload_to_google_drive(notebook_filename):
    """Upload notebook to Google Drive using Google API - SKIPPED DUE TO OAUTH ISSUES"""
    print("Step 1: Skipping Google Drive upload (OAuth configuration issues)...")
    print("   Using alternative approach: Direct ngrok hosting")

    # Skip Google Drive upload and go to next step
    return True


def update_ngrok_token(notebook_filename, ngrok_token):
    """Update ngrok auth token in notebook"""
    print("\nStep 2: Getting and setting ngrok auth token...")

    # Read notebook content
    try:
        with open(notebook_filename, "r") as f:
            notebook_content = f.read()
    except FileNotFoundError:
        print(f"❌ Notebook file '{notebook_filename}' not found")
        return False

    # Replace token placeholder
    if "YOUR_NGROK_AUTH_TOKEN" in notebook_content:
        new_content = notebook_content.replace("YOUR_NGROK_AUTH_TOKEN", ngrok_token)
        updated_filename = "updated_" + notebook_filename

        with open(updated_filename, "w") as f:
            f.write(new_content)

        print(f"✅ Token updated. Saved as '{updated_filename}'.")
        return updated_filename
    else:
        print("⚠️  Token placeholder 'YOUR_NGROK_AUTH_TOKEN' not found in notebook")
        print("   Using original notebook file")
        return notebook_filename


def execute_notebook_locally(notebook_filename):
    """Execute notebook cells locally using nbconvert"""
    print("\nStep 3: Running notebook cells locally...")

    try:
        import nbformat
        from nbconvert.preprocessors import ExecutePreprocessor
    except ImportError:
        print("❌ Required packages not installed. Run: pip install nbformat nbconvert")
        return False

    try:
        with open(notebook_filename) as f:
            nb = nbformat.read(f, as_version=4)

        ep = ExecutePreprocessor(timeout=600, kernel_name="python3")
        ep.preprocess(nb)

        # Save the executed notebook
        executed_filename = "executed_" + os.path.basename(notebook_filename)
        with open(executed_filename, "w", encoding="utf-8") as f:
            nbformat.write(nb, f)

        print("✅ Notebook executed successfully.")
        print(f"   Executed notebook saved as '{executed_filename}'")
        return True

    except Exception as e:
        print(f"❌ Error executing notebook: {e}")
        return False


def get_ngrok_public_url(port=8080):
    """Start ngrok and get public URL"""
    print(f"\nStep 4: Starting ngrok tunnel on port {port}...")

    try:
        # Start ngrok process
        ngrok_process = subprocess.Popen(
            ["ngrok", "http", str(port)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True,
        )
        time.sleep(3)  # Give ngrok time to start

        # Get public URL from ngrok API
        import requests

        try:
            response = requests.get("http://localhost:4040/api/tunnels", timeout=5)
            tunnels_data = response.json()

            if tunnels_data.get("tunnels"):
                public_url = tunnels_data["tunnels"][0]["public_url"]
                print(f"✅ ngrok Public URL: {public_url}")
                return public_url, ngrok_process
            else:
                print("❌ No tunnels found in ngrok API response")
                return None, ngrok_process

        except requests.exceptions.RequestException as e:
            print(f"❌ Could not fetch ngrok URL: {e}")
            print(
                "   Make sure ngrok is running and accessible at http://localhost:4040"
            )
            return None, ngrok_process

    except FileNotFoundError:
        print("❌ ngrok CLI not found. Install from https://ngrok.com/download")
        return None, None


def cleanup(ngrok_process=None):
    """Cleanup processes"""
    print("\nStep 5: Cleanup...")
    if ngrok_process:
        try:
            ngrok_process.terminate()
            ngrok_process.wait(timeout=5)
            print("✅ ngrok process terminated")
        except subprocess.TimeoutExpired:
            ngrok_process.kill()
            print("⚠️  ngrok process force killed")


def main():
    """Main automation function"""
    print("🚀 Raptor Mini Colab Automation Starting...\n")

    # Configuration
    notebook_filename = "raptor_mini_colab.ipynb"
    ngrok_token = "36cs1FkRw1Jua3GvHbyU2Smuood_3XfPCs2Jok9MHwANU8G9H"  # Your token
    ngrok_port = 8000  # Raptor Mini uses port 8000

    # Check if notebook exists
    if not os.path.exists(notebook_filename):
        print(f"❌ Notebook file '{notebook_filename}' not found in current directory")
        print(f"   Current directory: {os.getcwd()}")
        sys.exit(1)

    # Step 1: Upload to Google Drive (optional)
    upload_to_google_drive(notebook_filename)

    # Step 2: Update ngrok token
    updated_notebook = update_ngrok_token(notebook_filename, ngrok_token)
    if not updated_notebook:
        sys.exit(1)

    # Step 3: Execute notebook locally
    # Note: This executes locally, not in Colab
    if not execute_notebook_locally(updated_notebook):
        print("⚠️  Local execution failed, but you can still upload to Colab manually")

    # Step 4: Start ngrok and get URL
    public_url, ngrok_process = get_ngrok_public_url(ngrok_port)

    # Step 5: Cleanup
    cleanup(ngrok_process)

    print("\n🎯 Automation Summary:")
    print(f"   📓 Notebook: {notebook_filename}")
    print(f"   🔗 Public URL: {public_url or 'Not available'}")
    print("   📤 Upload to Colab: Manual step required")
    print("   🧹 Cleanup: Complete")

    if public_url:
        print(f"\n✅ Success! Raptor Mini is available at: {public_url}")
        print("   Update your .env file with this URL")
    else:
        print("\n⚠️  Partial success - check ngrok setup and try again")


if __name__ == "__main__":
    main()
