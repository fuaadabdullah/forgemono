#!/bin/bash
# Goblin Backend Configuration Update Script
# This script updates the backend configuration for API, CORS, and restarts the service

set -e

BACKEND_DIR="/root/goblin-assistant/api"
SERVER_IP="45.61.51.220"

echo "🔧 Updating Goblin Backend Configuration..."
echo "============================================"

# Update environment variables on server
echo "📝 Setting environment variables on server..."

ssh root@$SERVER_IP << 'EOF'
# Set the API key that matches the frontend
export LOCAL_LLM_API_KEY="206e61fdeda2267c9a4ecac3997c4eae7ebd20038282445f7524a84a78ac0158"

# Set CORS allowed origins for production
export ALLOWED_ORIGINS="https://goblin-frontend-dbmabskxk-fuaadabdullahs-projects.vercel.app,http://localhost:3000,http://localhost:8003"

# Set production environment
export ENVIRONMENT="production"

# Create/update .env file
cat > $BACKEND_DIR/.env << 'ENVEOF'
LOCAL_LLM_API_KEY=206e61fdeda2267c9a4ecac3997c4eae7ebd20038282445f7524a84a78ac0158
ALLOWED_ORIGINS=https://goblin-frontend-dbmabskxk-fuaadabdullahs-projects.vercel.app,http://localhost:3000,http://localhost:8003
ENVIRONMENT=production
DEBUG=false
EOF

echo "✅ Environment variables set"

# Check if service is running and restart
echo "🔄 Checking and restarting backend service..."

# Try systemd first
if command -v systemctl &> /dev/null; then
    if systemctl is-active --quiet goblin-backend 2>/dev/null; then
        echo "   Restarting goblin-backend via systemctl..."
        systemctl restart goblin-backend
        echo "✅ Service restarted via systemctl"
    else
        echo "   systemd service not found, using manual start..."
        pkill -f "uvicorn main:app" 2>/dev/null || true
        sleep 2
        cd $BACKEND_DIR
        nohup python -m uvicorn main:app --host 0.0.0.0 --port 8003 > /var/log/goblin-backend.log 2>&1 &
        echo "✅ Backend started on port 8003"
        sleep 3
    fi
else
    echo "   systemd not available, using manual start..."
    pkill -f "uvicorn main:app" 2>/dev/null || true
    sleep 2
    cd $BACKEND_DIR
    nohup python -m uvicorn main:app --host 0.0.0.0 --port 8003 > /var/log/goblin-backend.log 2>&1 &
    echo "✅ Backend started on port 8003"
    sleep 3
fi

# Verify service is running
echo "🔍 Verifying backend is running..."
if curl -s http://localhost:8003/health > /dev/null 2>&1; then
    echo "✅ Backend health check passed!"
    curl -s http://localhost:8000/health
else
    echo "⚠️  Health check failed, checking logs..."
    tail -20 /var/log/goblin-backend.log 2>/dev/null || echo "No logs available"
fi

echo ""
echo "============================================"
echo "✅ Backend configuration complete!"
EOF

echo ""
echo "🧪 Testing local connectivity..."
curl -s http://$SERVER_IP:8000/health || echo "Note: Router on 8000 may have different health endpoint"
