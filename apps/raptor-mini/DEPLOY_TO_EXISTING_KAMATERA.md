# Raptor Mini - Manual Deployment to Existing Kamatera Server

## Prerequisites

1. **SSH Access**: You need SSH access to your Kamatera server (66.55.77.147)
2. **Docker**: Docker must be installed on the Kamatera server
3. **Git**: Git must be available on the Kamatera server

## Step 1: Set up SSH Key Authentication (One-time)

On your **local machine**, copy the generated public key:

```bash
# Display the public key
cat ~/.ssh/kamatera_raptor.pub
```

On your **Kamatera server** (66.55.77.147), add the key to authorized_keys:

```bash
# SSH into your Kamatera server first (using password)
ssh root@66.55.77.147

# Then add the public key
echo "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIEJS/cwpwb8MA+ckZZRhbvyzylS7EOx7pNv1dTDY9iq9 raptor-mini-deploy" >> ~/.ssh/authorized_keys

# Set proper permissions
chmod 600 ~/.ssh/authorized_keys
chmod 700 ~/.ssh

# Exit and test key-based auth
exit
ssh -i ~/.ssh/kamatera_raptor root@66.55.77.147 "echo 'SSH key authentication working!'"
```

## Step 2: Deploy Raptor Mini

Once SSH key authentication is working, run the deployment:

```bash
# From your local machine, in the raptor-mini directory
cd /Users/fuaadabdullah/ForgeMonorepo/apps/raptor-mini

# Run the deployment script
./deploy-kamatera.sh
```

## Step 3: Manual Deployment (Alternative)

If the automated script doesn't work, deploy manually:

### On Kamatera Server (66.55.77.147):

```bash
# Update system and install dependencies
apt update && apt install -y docker.io git curl

# Create directory for Raptor Mini
mkdir -p /opt/raptor-mini
cd /opt/raptor-mini

# Clone or copy the raptor-mini code
# (You'll need to upload the files or use git)
git clone https://github.com/your-repo/raptor-mini.git .  # Adjust URL

# Generate API key
API_KEY=$(openssl rand -hex 32)
echo "Generated API Key: $API_KEY"
echo "Save this key for API access!"

# Stop existing container if running
docker stop raptor-mini 2>/dev/null || true
docker rm raptor-mini 2>/dev/null || true

# Build and run
docker build -t raptor-mini:latest .
docker run -d --name raptor-mini \
  -p 127.0.0.1:8080:8080 \
  -e API_KEY="$API_KEY" \
  -e MODEL_NAME="raptor-mini" \
  --restart unless-stopped \
  raptor-mini:latest

# Wait and test
sleep 10
curl -f http://127.0.0.1:8080/health
```

## Step 4: Verify Deployment

### Test Health Check:
```bash
# On Kamatera server
curl http://127.0.0.1:8080/health
# Should return: {"ok": true, "model": "raptor-mini"}
```

### Test API Generation:
```bash
# On Kamatera server
curl -X POST "http://127.0.0.1:8080/v1/generate" \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello world", "max_tokens": 50}'
```

### Check Logs:
```bash
# On Kamatera server
docker logs raptor-mini
```

## Step 5: Update Goblin Backend

The inference client is already configured to use your existing Kamatera setup. Make sure these environment variables are set in your Goblin backend:

```bash
# These should already be configured
KAMATERA_HOST=66.55.77.147
KAMATERA_LLM_API_KEY=goblin-llm-hrDD-3IO83-YpusDBHXV_V0r7Lx9sMtvEs4CWBnF2kE
```

## Step 6: Test Integration

In your Goblin backend, test the Raptor Mini integration:

```python
from backend.inference_clients import call_raptor

# This should now use your Kamatera-hosted Raptor Mini
result = await call_raptor("Test prompt", max_tokens=50)
print(result)
```

## Troubleshooting

### SSH Issues:
```bash
# Test SSH connection
ssh -i ~/.ssh/kamatera_raptor root@66.55.77.147 "echo 'Connection successful'"

# If key doesn't work, check server logs
ssh root@66.55.77.147 "tail -f /var/log/auth.log"
```

### Docker Issues:
```bash
# Check Docker status
ssh root@66.55.77.147 "systemctl status docker"

# Check container status
ssh root@66.55.77.147 "docker ps -a"
```

### API Issues:
```bash
# Check if service is responding
ssh root@66.55.77.147 "curl http://127.0.0.1:8080/health"

# Check container logs
ssh root@66.55.77.147 "docker logs raptor-mini"
```

## Security Notes

- Raptor Mini runs on port 8080 (your existing LLM uses 8000)
- API key authentication is required
- Service is bound to localhost only (127.0.0.1)
- No external access without proper proxy configuration

## Monitoring

- Health checks: `GET /health`
- Logs: `docker logs raptor-mini`

## Next Steps

1. Set up SSH key authentication
2. Deploy Raptor Mini using the script or manual steps
3. Test the API endpoints
4. Verify Goblin backend integration
5. Set up monitoring and alerts
