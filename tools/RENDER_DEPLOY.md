# Deploying FastAPI backend to Render (simple, low-cost option)

Render is a simple and affordable hosting option for FastAPI applications. The free tier or low-tier paid plans are typically cheaper than upgrading a Vercel team for extra serverless functions.

Quick steps:

1. Create an account on <https://render.com/> (Free tier available)
1. Add a new Web Service (not a Static Site):
   - Set 'Environment' to `Python`
   - Set the build command (for example): `pip install -r requirements.txt`
   - Set the start command: `uvicorn backend.app:app --host 0.0.0.0 --port $PORT`
1. Connect the project to your GitHub / GitLab / Bitbucket repo
1. Configure the environment variables for your application on Render (VITE_FASTAPI_URL is not needed server-side; instead set secret keys used by the backend; set CORS domains, etc.)
1. Deploy: Render will automatically build and deploy the service on push

Update the frontend (Vercel) to use Render’s URL:

```bash
vercel env add VITE_FASTAPI_URL https://your-backend.onrender.com --prod --team "YourTeam"
```

Important notes:
- If you deploy to Render's free plan, it may sleep after inactivity. For production uptime consider the paid hobby plan.
- This preserves your frontend on Vercel (Hobby) and moves CPU-bound functions to Render where they do not count as serverless functions on Vercel.

Verification (after deploy):
- See Render web console for service logs and health
- Test an endpoint: curl https://your-backend.onrender.com/health
- Check CORS and envs, then test Vercel frontend with `VITE_FASTAPI_URL` pointing to Render
