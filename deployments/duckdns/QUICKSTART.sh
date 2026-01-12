#!/bin/bash
#
# Quick Start: Configure DuckDNS for Vercel + Fly.io
#

cat << 'EOF'

╔════════════════════════════════════════════════════════════════╗
║                                                                ║
║   🚀 GoblinOS Assistant - Quick Domain Setup                  ║
║                                                                ║
╚════════════════════════════════════════════════════════════════╝

📋 What You Need to Do:

1️⃣  VERCEL - Add Custom Domain
   ─────────────────────────────────────────────────────────────
   • Go to: https://vercel.com → Your Project → Settings → Domains
   • Add: goblinosassistant.duckdns.org
   • Copy the IP address Vercel gives you (e.g., 76.76.21.21)

2️⃣  DUCKDNS - Point to Vercel
   ─────────────────────────────────────────────────────────────
   • Go to: https://www.duckdns.org/domains
   • Find: goblinosassistant
   • Update IP to the Vercel IP from step 1
   • Click "update ip"

3️⃣  VERCEL - Update Environment Variables
   ─────────────────────────────────────────────────────────────
   Settings → Environment Variables:
   
   BACKEND_URL=https://goblin-backend.fly.dev
   NEXT_PUBLIC_API_URL=https://goblin-backend.fly.dev
   NEXT_PUBLIC_DOMAIN=goblinosassistant.duckdns.org

4️⃣  DEPLOY - Push Changes
   ─────────────────────────────────────────────────────────────
   cd apps/goblin-assistant
   git add vercel.json
   git commit -m "feat: Configure DuckDNS with Fly.io backend"
   git push
   
   (Vercel will auto-deploy)

5️⃣  VERIFY - Test Everything
   ─────────────────────────────────────────────────────────────
   # Backend health
   curl https://goblin-backend.fly.dev/health
   
   # Frontend
   curl -I https://goblinosassistant.duckdns.org

✅ Your Architecture:

   Customer
      ↓
   goblinosassistant.duckdns.org (Vercel IP)
      ↓
   Frontend (Vercel)
      ↓
   goblin-backend.fly.dev
      ↓
   Backend (Fly.io)

📚 Full Instructions:
   deployments/duckdns/VERCEL_FLYIO_SETUP.md

🎯 Ready in 10 minutes!

EOF
