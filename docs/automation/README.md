# Raptor Mini Colab Automation

This script automates the deployment of Raptor Mini to Google Colab with ngrok tunneling.

## Google API Setup (Required)

Before running the script, you must set up OAuth credentials to allow programmatic access to Google Drive and Colab.

### 1. Enable APIs in Google Cloud Console

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the following APIs:
   - **Google Drive API**
   - **Google Colab API** (if available)

### 2. Create OAuth 2.0 Credentials

1. In the Google Cloud Console, go to **APIs & Services > Credentials**
2. Click **+ CREATE CREDENTIALS > OAuth 2.0 Client IDs**
3. Choose **Desktop application** as the application type
4. Download the credentials JSON file
5. Save it as `credentials.json` in the same directory as the script

### 4. Test Setup (Optional)

Use the setup helper script to verify your configuration:

```bash
# Check if credentials are set up
python setup_google_oauth.py --check

# Test Google API connectivity
python setup_google_oauth.py --test

# Create credentials template
python setup_google_oauth.py --template

# Open Google Cloud Console
python setup_google_oauth.py --console

# Show detailed instructions
python setup_google_oauth.py --help
```

## Features

- 🔄 **Automated Setup**: Updates ngrok auth token in notebook
- 🚀 **Local Execution**: Runs notebook cells locally using nbconvert
- 🌐 **Ngrok Integration**: Starts ngrok tunnel and extracts public URL
- 🧹 **Cleanup**: Properly terminates processes

## Prerequisites

### Required Tools
- Python 3.7+
- ngrok CLI (`brew install ngrok` or download from https://ngrok.com)
- gdrive CLI (optional, for Google Drive upload)

### Python Dependencies
```bash

pip install -r requirements-automation.txt
```

## Usage

### 1. Configure ngrok

```bash
ngrok config add-authtoken YOUR_TOKEN_HERE
```

### 2. Run Automation
```bash

python automate_raptor_colab.py
```

## What It Does

1. **Upload to Google Drive** (optional)
   - Uses gdrive CLI if available
   - Skips if gdrive not installed

2. **Update Auth Token**
   - Replaces `YOUR_NGROK_AUTH_TOKEN` in notebook
   - Saves as `updated_raptor_mini_colab.ipynb`

3. **Execute Notebook Locally**
   - Runs all cells using nbconvert
   - Saves executed version as `executed_raptor_mini_colab.ipynb`

4. **Start ngrok Tunnel**
   - Launches ngrok on port 8000
   - Fetches public URL from ngrok API

5. **Cleanup**
   - Terminates ngrok process
   - Reports final status

## Output

```
🚀 Raptor Mini Colab Automation Starting...

Step 1: Uploading notebook to Google Drive...
✅ Upload successful: ...

Step 2: Getting and setting ngrok auth token...
✅ Token updated. Saved as 'updated_raptor_mini_colab.ipynb'.

Step 3: Running notebook cells locally...
✅ Notebook executed successfully.

Step 4: Starting ngrok tunnel on port 8000...
✅ ngrok Public URL: <https://abc123.ngrok.io>

🎯 Automation Summary:
   📓 Notebook: raptor_mini_colab.ipynb
   🔗 Public URL: <https://abc123.ngrok.io>
   📤 Upload to Colab: Manual step required
   🧹 Cleanup: Complete

✅ Success! Raptor Mini is available at: <https://abc123.ngrok.io>
```

## Important Notes

### Local vs Colab Execution

- This script executes the notebook **locally** using nbconvert
- For actual Colab execution, you still need to:
  1. Upload `updated_raptor_mini_colab.ipynb` to Google Colab
  2. Set environment variables in Colab runtime
  3. Run cells manually in Colab

### Colab API Limitations
Google Colab doesn't provide a public API for automated execution. This script provides the foundation but Colab execution requires manual steps.

### Security

- Auth tokens are handled securely (no hardcoded values)
- Environment variables are recommended for production
- ngrok processes are properly cleaned up

## Troubleshooting

### ngrok Issues

```bash
# Check if ngrok is running
curl http://localhost:4040/api/tunnels

# Kill existing ngrok processes
pkill ngrok
```

### Import Errors
```bash

pip install nbformat nbconvert requests
```

### Permission Issues

```bash
chmod +x automate_raptor_colab.py
```

## Files Created

- `automate_raptor_colab.py` - Complete automation script with Google API integration
- `setup_google_oauth.py` - OAuth setup helper and testing tool
- `requirements-automation.txt` - Python dependencies including Google APIs
- `credentials.json` - OAuth credentials template (replace with real credentials)
- `updated_raptor_mini_colab.ipynb` - Notebook with auth token (created after first run)
- `executed_raptor_mini_colab.ipynb` - Locally executed notebook (optional)

## Next Steps

After running this script:

1. Upload `updated_raptor_mini_colab.ipynb` to Google Colab
2. Set environment variables in Colab:
   - `NGROK_AUTH_TOKEN`: Your ngrok token
   - `RAPTOR_ENV`: Set to 'production'
3. Run all cells in Colab
4. Copy the ngrok URL from Colab output
5. Update your `.env` file with the Colab ngrok URL
