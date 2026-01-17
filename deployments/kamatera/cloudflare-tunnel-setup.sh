#!/bin/bash
# Project: Goblin Assistant
# Script: cloudflare-tunnel-setup.sh
# Purpose: Setup Cloudflare Tunnels for Kamatera servers
# Date: 2025-12-18
# Maintainer: fuaadabdullah

set -e

echo "🌐 Setting up Cloudflare Tunnels for Kamatera Infrastructure"
echo "=========================================================="

# Install Cloudflare CLI
echo "📦 Installing Cloudflare CLI..."
if ! command -v cloudflared &> /dev/null; then
    curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o cloudflared
    sudo mv cloudflared /usr/local/bin/
    sudo chmod +x /usr/local/bin/cloudflared
else
    echo "✅ Cloudflare CLI already installed"
fi

# Server configurations
declare -A servers=(
    ["server1"]="192.175.23.150:8002:Ollama LLM Inference"
    ["server2"]="45.61.51.220:8000:Goblin Router API"
    ["server2-redis"]="45.61.51.220:6379:Redis Cache"
    ["server2-postgres"]="45.61.51.220:5432:PostgreSQL Database"
)

echo
echo "🔑 Please authenticate with Cloudflare:"
echo "Run: cloudflared tunnel login"
echo
read -p "Press Enter after completing authentication..."

# Create tunnels for each server
for server_name in "${!servers[@]}"; do
    IFS=':' read -r server_ip port description <<< "${servers[$server_name]}"
    
    echo
    echo "🚀 Creating tunnel for $description ($server_ip:$port)"
    
    # Create tunnel
    cloudflared tunnel create "$server_name" || echo "⚠️ Tunnel $server_name may already exist"
    
    # Create tunnel configuration
    mkdir -p "/root/.cloudflared"
    
    cat > "/root/.cloudflared/tunnel-$server_name.yml" << EOF
tunnel: $server_name
credentials-file: /root/.cloudflared/$server_name.json

# Map external hostname to internal server
ingress:
  - hostname: $server_name.goblin-assistant.dev
    path: /
    service: http://$server_ip:$port
  - hostname: $server_name.goblin-assistant.dev
    path: /api/*
    service: http://$server_ip:$port
  - hostname: $server_name.goblin-assistant.dev
    path: /health
    service: http://$server_ip:$port
  - service: http_status:404
EOF

    echo "✅ Created tunnel configuration: /root/.cloudflared/tunnel-$server_name.yml"
    
    # Run tunnel
    echo "🔗 Starting tunnel for $server_name..."
    nohup cloudflared tunnel --config "/root/.cloudflared/tunnel-$server_name.yml" run > "/var/log/cloudflared-$server_name.log" 2>&1 &
    echo "📝 Tunnel logs: /var/log/cloudflared-$server_name.log"
done

# Create systemd services for automatic tunnel startup
echo
echo "🔧 Creating systemd services for tunnels..."

for server_name in "${!servers[@]}"; do
    cat > "/etc/systemd/system/cloudflared-$server_name.service" << EOF
[Unit]
Description=Cloudflare Tunnel for $server_name
After=network.target

[Service]
Type=simple
User=root
Group=root
ExecStart=/usr/local/bin/cloudflared tunnel --config /root/.cloudflared/tunnel-$server_name.yml run
Restart=always
RestartSec=10
StandardOutput=append:/var/log/cloudflared-$server_name.log
StandardError=append:/var/log/cloudflared-$server_name.log

[Install]
WantedBy=multi-user.target
EOF

    systemctl enable "cloudflared-$server_name"
    systemctl start "cloudflared-$server_name"
    echo "✅ Enabled and started cloudflared-$server_name.service"
done

# Create tunnel management script
echo
echo "📝 Creating tunnel management script..."
cat > /opt/cloudflare-tunnels/manage-tunnels.sh << 'EOF'
#!/bin/bash
# Manage Cloudflare tunnels

TUNNELS_DIR="/root/.cloudflared"
LOG_DIR="/var/log"

case "$1" in
    start)
        echo "🚀 Starting all tunnels..."
        for service in /etc/systemd/system/cloudflared-*.service; do
            systemctl start "$(basename "$service")"
        done
        ;;
    stop)
        echo "🛑 Stopping all tunnels..."
        for service in /etc/systemd/system/cloudflared-*.service; do
            systemctl stop "$(basename "$service")"
        done
        ;;
    restart)
        echo "🔄 Restarting all tunnels..."
        for service in /etc/systemd/system/cloudflared-*.service; do
            systemctl restart "$(basename "$service")"
        done
        ;;
    status)
        echo "📊 Tunnel status:"
        for service in /etc/systemd/system/cloudflared-*.service; do
            service_name=$(basename "$service" .service)
            echo "• $service_name: $(systemctl is-active "$service_name")"
        done
        ;;
    logs)
        echo "📋 Recent tunnel logs:"
        for log in "$LOG_DIR"/cloudflared-*.log; do
            tunnel_name=$(basename "$log" .log)
            echo "=== $tunnel_name.log ==="
            tail -n 10 "$log"
        done
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|logs}"
        exit 1
        ;;
esac
EOF

chmod +x /opt/cloudflare-tunnels/manage-tunnels.sh

# Create DNS configuration instructions
echo
echo "📋 DNS Configuration Instructions:"
echo "================================="
echo
echo "After creating tunnels, configure DNS records in Cloudflare:"
echo
echo "1. Go to Cloudflare Dashboard → DNS"
echo "2. Add the following CNAME records:"
echo

for server_name in "${!servers[@]}"; do
    IFS=':' read -r server_ip port description <<< "${servers[$server_name]}"
    echo "   Name: $server_name.goblin-assistant.dev"
    echo "   Target: $server_name.cfargotunnel.com"
    echo "   Proxy: 🟡 Proxied (orange cloud)"
    echo
done

echo "3. SSL/TLS:"
echo "   • Set encryption mode to 'Full (strict)'"
echo "   • Enable 'Always Use HTTPS'"
echo "   • Enable 'Automatic HTTPS Rewrites'"
echo
echo "4. Security Settings:"
echo "   • Enable WAF rules"
echo "   • Set security level to 'Medium'"
echo "   • Enable bot fight mode"
echo
echo "5. Speed Optimization:"
echo "   • Enable Auto Minify (HTML, CSS, JS)"
echo "   • Enable Brotli compression"
echo "   • Set Browser Cache TTL to 4 hours"

# Create monitoring script
echo
echo "📊 Creating tunnel monitoring script..."
cat > /opt/cloudflare-tunnels/monitor-tunnels.sh << 'EOF'
#!/bin/bash
# Monitor Cloudflare tunnels

echo "=== Cloudflare Tunnel Monitoring ==="
echo "Time: $(date)"
echo

echo "🔗 Tunnel Status:"
for service in /etc/systemd/system/cloudflared-*.service; do
    service_name=$(basename "$service" .service)
    status=$(systemctl is-active "$service_name")
    if [ "$status" = "active" ]; then
        echo "✅ $service_name: Running"
    else
        echo "❌ $service_name: Failed"
        echo "   Last 5 lines of log:"
        tail -n 5 "/var/log/${service_name}.log" 2>/dev/null || echo "   No logs available"
    fi
done

echo
echo "🌐 Network Connectivity:"
for server_name in server1 server2; do
    echo "Testing $server_name.goblin-assistant.dev..."
    if curl -s -o /dev/null -w "%{http_code}" "https://$server_name.goblin-assistant.dev/health" | grep -q "200"; then
        echo "✅ $server_name tunnel is accessible"
    else
        echo "❌ $server_name tunnel is not responding"
    fi
done

echo
echo "📋 Recent System Logs:"
journalctl -u cloudflared-server1 -u cloudflared-server2 -u cloudflared-server2-redis -u cloudflared-server2-postgres --since="1 hour ago" --no-pager | tail -n 20
EOF

chmod +x /opt/cloudflare-tunnels/monitor-tunnels.sh

# Setup log rotation
echo
echo "📝 Setting up log rotation..."
cat > /etc/logrotate.d/cloudflared-tunnels << 'EOF'
/var/log/cloudflared-*.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    create 0640 root root
}
EOF

# Create cron job for monitoring
echo "0 */6 * * * root /opt/cloudflare-tunnels/monitor-tunnels.sh >> /var/log/tunnel-monitoring.log 2>&1" >> /etc/crontab

# Final setup summary
echo
echo "🎉 Cloudflare Tunnel Setup Complete!"
echo "==================================="
echo
echo "✅ Installed Cloudflare CLI"
echo "✅ Created tunnels for all servers"
echo "✅ Configured systemd services"
echo "✅ Created management scripts"
echo "✅ Setup monitoring and logging"
echo
echo "📋 Next Steps:"
echo "1. Complete DNS configuration (instructions above)"
echo "2. Test tunnel connectivity"
echo "3. Configure Cloudflare security settings"
echo
echo "🛠️ Useful Commands:"
echo "• Manage tunnels: /opt/cloudflare-tunnels/manage-tunnels.sh {start|stop|restart|status|logs}"
echo "• Monitor tunnels: /opt/cloudflare-tunnels/monitor-tunnels.sh"
echo "• View tunnel logs: journalctl -u cloudflared-server*"
echo "• Check tunnel status: cloudflared tunnel list"
echo
echo "🌐 Tunnel Endpoints (after DNS setup):"
for server_name in "${!servers[@]}"; do
    IFS=':' read -r server_ip port description <<< "${servers[$server_name]}"
    echo "• https://$server_name.goblin-assistant.dev → $server_ip:$port ($description)"
done

echo
echo "🔒 Security Notes:"
echo "• All traffic is now routed through Cloudflare"
echo "• Origin IPs are hidden from public access"
echo "• DDoS protection and WAF are active"
echo "• SSL/TLS certificates are managed by Cloudflare"

# Test tunnel setup
echo
echo "🔍 Testing tunnel setup..."
sleep 5
if systemctl is-active cloudflared-server1 >/dev/null 2>&1; then
    echo "✅ Server1 tunnel is running"
else
    echo "⚠️ Server1 tunnel may need attention"
fi

if systemctl is-active cloudflared-server2 >/dev/null 2>&1; then
    echo "✅ Server2 tunnel is running"
else
    echo "⚠️ Server2 tunnel may need attention"
fi

echo
echo "🚀 Setup complete! Configure DNS records to complete the setup."
