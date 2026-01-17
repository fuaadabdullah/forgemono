---
title: "ALTERNATIVES_TO_VERCEL_PRO"
description: "Documentation for ALTERNATIVES_TO_VERCEL_PRO"
---



- Keep Vercel for frontend only; use CI to deploy the backend to Render/Fly. Update environment variables and DNS accordingly.

## Verification checklist (after migration or consolidation)

- Ensure `VITE_FASTAPI_URL` is set in Vercel (Team/Project) and points to the new backend URL
- Check that there are no serverless function files remaining in Vercel `api/` directory (or that they are combined into 1 or a few files)
- Deploy and verify that `window.location.hostname` fallback and local dev fallback aren't used for production
- For breaking security leaks, rotate keys and re-check logs

## Cost comparisons (rough estimates)

- Render: $0 to $7/mo for small web services; auto-sleeps when idle on the free plan
- DigitalOcean droplet: $4–$6/mo for small apps (single process)
- Cloud Run / GCP: pay per request/compute; usually cheaper for low-traffic sites
- Vercel: Hobby is free, Team Pro starts at 20 USD per seat (varies by region)

If you want, I can:

1. Draft a `tools/migrate-backend-to-render.sh` script that handles the basic Render CLI steps
2. Add a sample consolidated `api/index.ts` to the `tools/` directory (not deployed automatically)
3. Help replace current serverless functions in the repo with a consolidated router

End of document
