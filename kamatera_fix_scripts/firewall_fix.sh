#!/bin/bash
# Kamatera Firewall Fix Script
# Run this on BOTH servers to allow internal traffic

echo "🔧 Configuring Kamatera Firewall..."
echo "Server IPs: Inference=192.175.23.150, Router=45.61.51.220"

# Allow internal traffic
if command -v ufw >/dev/null 2>&1; then
    echo "Using UFW..."
    ufw allow from 45.61.51.220 to any port 8002
    ufw allow from 192.175.23.150 to any port 8000
    ufw --force reload
    echo "✅ UFW configured"
elif command -v firewall-cmd >/dev/null 2>&1; then
    echo "Using firewalld..."
    firewall-cmd --permanent --add-rich-rule="rule family='ipv4' source address='45.61.51.220' port protocol='tcp' port='8002' accept"
    firewall-cmd --permanent --add-rich-rule="rule family='ipv4' source address='192.175.23.150' port protocol='tcp' port='8000' accept"
    firewall-cmd --reload
    echo "✅ firewalld configured"
else
    echo "⚠️  No firewall tool found. Configure manually to allow ports 8002 and 8000"
    echo "Run these commands manually:"
    echo "  iptables -A INPUT -s 45.61.51.220 -p tcp --dport 8002 -j ACCEPT"
    echo "  iptables -A INPUT -s 192.175.23.150 -p tcp --dport 8000 -j ACCEPT"
fi

echo "Next: sudo systemctl restart local-llm-proxy goblin-router"