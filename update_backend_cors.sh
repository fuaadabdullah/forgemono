#!/bin/bash

# Backend CORS Configuration Update Script
# This script updates the backend server to allow CORS from the Vercel frontend

echo "🔧 Updating Backend CORS Configuration..."

# Vercel frontend URL
VERCEL_URL="https://goblin-frontend-2gqt5mqg7-fuaadabdullahs-projects.vercel.app"

# Backend server details
BACKEND_HOST="45.61.51.220"
BACKEND_USER="root"

echo "📝 Setting ALLOWED_ORIGINS environment variable..."
echo "   Vercel Frontend URL: $VERCEL_URL"
echo "   Backend Server: $BACKEND_HOST"

# Create a temporary script to run on the backend server
cat << 'EOF' > temp_cors_update.sh
#!/bin/bash

# Backup existing environment if it exists
if [ -f /etc/environment ]; then
    echo "📋 Backing up /etc/environment..."
    sudo cp /etc/environment /etc/environment.backup.$(date +%Y%m%d_%H%M%S)
fi

# Update or create the environment file with CORS settings
echo "🔧 Updating environment configuration..."

# Create environment file with proper CORS settings
sudo tee /etc/environment > /dev/null << ENVEOF
# Production Environment Configuration
ENVIRONMENT=production
ALLOWED_ORIGINS=https://goblin-frontend-2gqt5mqg7-fuaadabdullahs-projects.vercel.app,http://localhost:3000
# Backend API Configuration
API_HOST=0.0.0.0
API_PORT=8001
# Other production settings
LOG_LEVEL=INFO
ENVEOF

echo "✅ Environment configuration updated"
echo "📄 Current ALLOWED_ORIGINS configuration:"
grep "ALLOWED_ORIGINS" /etc/environment || echo "   ALLOWED_ORIGINS not found in /etc/environment"

# Also update any .env files in the project directory
echo "🔍 Checking for .env files to update..."
find /opt -name ".env" -type f 2>/dev/null | while read env_file; do
    echo "📝 Updating $env_file..."
    sudo tee "$env_file" > /dev/null << ENVEOF
ENVIRONMENT=production
ALLOWED_ORIGINS=https://goblin-frontend-2gqt5mqg7-fuaadabdullahs-projects.vercel.app,http://localhost:3000
API_HOST=0.0.0.0
API_PORT=8001
LOG_LEVEL=INFO
ENVEOF
done

# Create systemd service override for the backend service
echo "🔧 Creating systemd service override..."
sudo mkdir -p /etc/systemd/system/goblin-backend.service.d/
sudo tee /etc/systemd/system/goblin-backend.service.d/cors-update.conf > /dev/null << SERVICEOF
[Service]
Environment="ALLOWED_ORIGINS=https://goblin-frontend-2gqt5mqg7-fuaadabdullahs-projects.vercel.app,http://localhost:3000"
Environment="ENVIRONMENT=production"
SERVICEOF

echo "✅ Systemd service override created"

# Reload systemd and restart the service
echo "🔄 Reloading systemd configuration..."
sudo systemctl daemon-reload

echo "🔄 Restarting goblin-backend service..."
if sudo systemctl is-active --quiet goblin-backend; then
    sudo systemctl restart goblin-backend
    echo "✅ Backend service restarted successfully"
else
    echo "⚠️  goblin-backend service is not running, attempting to start..."
    sudo systemctl start goblin-backend
fi

# Wait a moment for the service to start
sleep 3

# Check service status
echo "🔍 Checking backend service status..."
if sudo systemctl is-active --quiet goblin-backend; then
    echo "✅ Backend service is running"
    echo "📊 Service status:"
    sudo systemctl status goblin-backend --no-pager -l
else
    echo "❌ Backend service is not running"
    echo "📊 Service status:"
    sudo systemctl status goblin-backend --no-pager -l
fi

# Test the backend health endpoint
echo "🏥 Testing backend health endpoint..."
if curl -f -s http://localhost:8001/health > /dev/null; then
    echo "✅ Backend health endpoint is accessible"
else
    echo "⚠️  Backend health endpoint is not accessible"
fi

echo "🎉 CORS configuration update completed!"
echo "📝 Summary:"
echo "   - Vercel frontend URL: https://goblin-frontend-2gqt5mqg7-fuaadabdullahs-projects.vercel.app"
echo "   - Environment: production"
echo "   - Backend service: $(sudo systemctl is-active goblin-backend)"
echo ""
echo "🔍 You can verify CORS settings by checking the backend logs:"
echo "   sudo journalctl -u goblin-backend -f"

EOF

# Copy the script to the backend server and execute it
echo "📤 Copying CORS update script to backend server..."
scp -o StrictHostKeyChecking=no temp_cors_update.sh $BACKEND_USER@$BACKEND_HOST:/tmp/

if [ $? -eq 0 ]; then
    echo "✅ Script copied successfully"
    echo "🔧 Executing CORS update on backend server..."
    ssh -o StrictHostKeyChecking=no $BACKEND_USER@$BACKEND_HOST "chmod +x /tmp/temp_cors_update.sh && /tmp/temp_cors_update.sh"
    
    echo "🧹 Cleaning up temporary files..."
    rm temp_cors_update.sh
    ssh -o StrictHostKeyChecking=no $BACKEND_USER@$BACKEND_HOST "rm -f /tmp/temp_cors_update.sh"
    
    echo "🎉 Backend CORS configuration update completed!"
else
    echo "❌ Failed to copy script to backend server"
    echo "🧹 Cleaning up temporary files..."
    rm temp_cors_update.sh
fi

echo ""
echo "📋 Next Steps:"
echo "1. Verify the backend service is running: ssh $BACKEND_USER@$BACKEND_HOST 'systemctl status goblin-backend'"
echo "2. Test the frontend-backend connection: curl -H 'Origin: https://goblin-frontend-2gqt5mqg7-fuaadabdullahs-projects.vercel.app' http://$BACKEND_HOST:8001/health"
echo "3. Access the frontend at: https://goblin-frontend-2gqt5mqg7-fuaadabdullahs-projects.vercel.app"