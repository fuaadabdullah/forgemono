ALTERNATIVES TO VERCEL PRO (Avoid paying for Pro plan)
===============================================

This file summarizes practical, low-cost alternatives to upgrading to the Vercel Pro plan while keeping your app fully functional and avoiding the 12-serverless-function limit.

Important security step — exposed API key
----------------------------------------
- You must revoke/regenerate any API keys that have been posted or leaked. The token in your conversation appears to be a Google-style API key.
- Steps to rotate/revoke:
  - Google Cloud Console: Menu → APIs & Services → Credentials → find the key → Delete/Regenerate.
  - Vercel Console: Project → Settings → Environment Variables → Update values to the new key.
  - Git: Remove the key from commits if it was committed (see suggestions below).

If the key was in a commit, rotate it and then: (example; use your tooling)

```bash
# Replace <OLD_KEY> with the key to remove; update `--path` as needed
git filter-repo --replace-refs delete-no-add --invert-paths --path <file-containing-key>
git push origin --force
```

Do not commit secrets to the repository. Use Vercel env variables or CI secrets for all runtime secrets.

1) Best short-term: Host your backend externally and keep static front end on Vercel
-------------------------------------------------------------------------
- Quick win: Host your entire API server (FastAPI) to Render / Railway / Fly / DigitalOcean App Platform / Cloud Run and point your Vercel frontend at the external URL via environment variables.
- This reduces Vercel's serverless function usage to zero and keeps Vercel free for static hosting.

Advantages:
- Low cost and fast to set up
- Full control and no per-deployment function limit
- Keep UI hosted on Vercel while the backend runs on Render/Heroku/Cloud Run.

Render example (FastAPI):
1. Create a Render account and a new Web Service
2. Connect the repo and configure the `start` command (like `uvicorn backend.app:app --host 0.0.0.0 --port $PORT`)
3. Add environment variables under Render's dashboard: `VITE_FASTAPI_URL` etc.
4. Update Vercel project env variable `VITE_FASTAPI_URL` to the Render URL (via UI or CLI):

```bash
vercel env add VITE_FASTAPI_URL https://your-backend.onrender.com --prod --team "YourTeam"
```

2) Consolidate many Vercel Serverless Functions into one or a few functions (technical approach)
---------------------------------------------------------------------------------------------
- If your Vercel deployment uses many serverless function files under `/api` (each file counts), you can combine them into a single file router to reduce the count drastically.
- Keep your existing logic in small modules (handlers) and import them into a single `api/index.js|ts` route that maps paths to handlers.

High-level steps:
1. Move all small handlers into `lib/handlers/<name>.ts` or similar
2. Create `api/index.ts` that inspects `req.url` and `req.method` and dispatches to the proper handler
3. Deploy the single function — it can handle all existing endpoints internally

Sample `api` router (Node/TypeScript) — put in your target Vercel project's `/api/index.ts` (example only):

```ts
import type { VercelRequest, VercelResponse } from '@vercel/node'
import { handlerA } from '../lib/handlers/a'
import { handlerB } from '../lib/handlers/b'

const routes = new Map([
  ['/api/item', handlerA],
  ['/api/other', handlerB],
])

export default function (req: VercelRequest, res: VercelResponse) {
  const path = new URL(req.url ?? '/', `http://${req.headers.host}`).pathname
  const route = routes.get(path)
  if (!route) {
    res.status(404).json({ error: 'Not found' })
    return
  }
  return route(req, res)
}
```

Pros:
- No need to upgrade; you reduce the serverless function count
- Minimal runtime logic changes — you reorganize but not reimplement

Cons:
- Slightly more complicated deployment logic, dev ergonomics may change (local dev must consider the router)

3) Move to another host entirely for both front and backend (cheapest options)
--------------------------------------------------------------------------
- Netlify: Netlify has function limits on hobby, but it often provides free tiers. Additional functions cost money.
- Render: Provides both web services and background workers; free tier for backend web services; easy to deploy and configure.
- Railway: Good for fast prototypes; free tier and easy deployment.
- Fly.io: Deploys containers; you can run a single container for many endpoints.
- Cloud Run / Cloud Functions: Pay-as-you-go; can be cheap for small loads; unlimited endpoints via a single server container

Pros:
- Potentially cheaper than an upgrade if you can host your whole backend on a $5–$7/month VM/container

4) Split your app into fewer functions and static assets
---------------------------------------------------
- If the function files are created by route-specific files, combine functionality into fewer files (e.g., `api/action.ts` that accepts the path or an `action` parameter).

5) Use an HTTP proxy / edge worker
----------------------------------
- Use Cloudflare Workers to aggregate, route, and proxy calls to a small backend. Cloudflare Workers free tier is generous, and its Workers KV and durable storage can help. Or use CloudFront / API Gateway.

6) Self-host on a cheap instance / container
-------------------------------------------
- For small teams, a $5/month DigitalOcean droplet or $3–$7/month server (Hetzner) can run Uvicorn + FastAPI and manage all endpoints in one process.

7) Adjust the CI/CD deployment to push all server functions to a single service
---------------------------------------------------------------------------
- Keep Vercel for frontend only; use CI to deploy the backend to Render/Fly. Update environment variables and DNS accordingly.

Verification checklist (after migration or consolidation)
--------------------------------------------------------
- Ensure `VITE_FASTAPI_URL` is set in Vercel (Team/Project) and points to the new backend URL
- Check that there are no serverless function files remaining in Vercel `api/` directory (or that they are combined into 1 or a few files)
- Deploy and verify that `window.location.hostname` fallback and local dev fallback aren't used for production
- For breaking security leaks, rotate keys and re-check logs

Cost comparisons (rough estimates)
---------------------------------
- Render: $0 to $7/mo for small web services; auto-sleeps when idle on the free plan
- DigitalOcean droplet: $4–$6/mo for small apps (single process)
- Cloud Run / GCP: pay per request/compute; usually cheaper for low-traffic sites
- Vercel: Hobby is free, Team Pro starts at 20 USD per seat (varies by region)

If you want, I can:
1) Draft a `tools/migrate-backend-to-render.sh` script that handles the basic Render CLI steps
2) Add a sample consolidated `api/index.ts` to the `tools/` directory (not deployed automatically)
3) Help replace current serverless functions in the repo with a consolidated router

End of document
