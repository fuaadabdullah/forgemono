#!/bin/bash
echo "🔐 Adding Chromatic Project Token to Bitwarden..."

# Check if BW is unlocked
if ! bw status | grep -q '"status":"unlocked"'; then
    echo "❌ Bitwarden CLI is locked. Please unlock it first:"
    echo "   bw unlock"
    exit 1
fi

# Add the token as a login item
echo '{"type":1,"name":"goblin-prod-chromatic-token","login":{"username":"chromatic","password":"chpt_00986f31d4d33a1"}}' | bw create item

if [ $? -eq 0 ]; then
    echo "✅ Chromatic token added successfully!"
    echo "🎨 Chromatic integration is now complete!"
else
    echo "❌ Failed to add token"
    exit 1
fi
