#!/bin/bash

# Raptor Mini - SSH Setup Helper
# Helps set up SSH key authentication for Kamatera deployment

echo "🔐 Raptor Mini - SSH Setup for Kamatera"
echo "======================================"

# Check if SSH key exists
if [ ! -f ~/.ssh/kamatera_raptor ]; then
    echo "❌ SSH key not found. Run this first:"
    echo "ssh-keygen -t ed25519 -C 'raptor-mini-deploy' -f ~/.ssh/kamatera_raptor -N ''"
    exit 1
fi

echo "✅ SSH key found"

# Display public key
echo ""
echo "📋 Copy this public key to your Kamatera server (66.55.77.147):"
echo ""
cat ~/.ssh/kamatera_raptor.pub
echo ""
echo "📝 On your Kamatera server, run these commands:"
echo ""
echo "   # Add the key above to authorized_keys"
echo "   echo 'PASTE_THE_KEY_HERE' >> ~/.ssh/authorized_keys"
echo "   chmod 600 ~/.ssh/authorized_keys"
echo "   chmod 700 ~/.ssh"
echo ""

# Test connection
echo "🧪 Testing SSH connection..."
if ssh -i ~/.ssh/kamatera_raptor -o ConnectTimeout=10 -o BatchMode=yes root@66.55.77.147 "echo 'SSH connection successful!'" 2>/dev/null; then
    echo "✅ SSH key authentication working!"
    echo ""
    echo "🚀 Ready to deploy! Run:"
    echo "   cd /Users/fuaadabdullah/ForgeMonorepo/apps/raptor-mini"
    echo "   ./deploy-kamatera.sh"
else
    echo "❌ SSH connection failed. Make sure:"
    echo "   - You copied the public key to the server"
    echo "   - The server is accessible"
    echo "   - SSH service is running on Kamatera"
fi
