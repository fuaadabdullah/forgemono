# 🎯 Add Custom Domain - Step-by-Step

**I've opened the exact page for you!**

You should now see the **Triggers** page with "Custom Domains" section.

---

## Quick Steps

1. Scroll down to **"Custom Domains"** section
2. You'll see a button **"Add Custom Domain"** or **"+ Add"**
3. Click it
4. A dialog will appear asking for the hostname
5. Enter: `brain.goblin.fuaad.ai`
6. Click **"Add Custom Domain"** or **"Save"**

---

## What Happens

Cloudflare will:
- ✅ Automatically create the DNS record for `brain.goblin.fuaad.ai`
- ✅ Point it to your Worker
- ✅ Enable proxying (orange cloud)
- ✅ Provision an SSL certificate
- ✅ Make `brain.goblin.fuaad.ai` route to your Worker

---

## Expected Result

After adding, you should see:

```
Custom Domains
brain.goblin.fuaad.ai  ✅ Active
```

---

## After This

You'll still need to add the other 3 DNS records manually:
- `goblin.fuaad.ai` → `goblin-assistant.fly.dev`
- `api.goblin.fuaad.ai` → `goblin-assistant-backend.onrender.com`
- `ops.goblin.fuaad.ai` → `9c780bd1-ac63-4d6c-afb1-787a2867e5dd.cfargotunnel.com`

**See: `DNS_RECORDS_CHEATSHEET.md`**

---

**Do this now, then let me know when done!** ✨
