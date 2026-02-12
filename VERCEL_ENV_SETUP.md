# Vercel Environment Variables Setup

## Variables to Add

Go to your Vercel project dashboard and add these environment variables:

### 1. NEXT_PUBLIC_API_URL
- **Value**: `https://goblin-backend.fly.dev`
- **Environment**: Production
- **Description**: Backend API endpoint for the Goblin Assistant

### 2. NEXT_PUBLIC_FASTAPI_URL
- **Value**: `https://goblin-backend.fly.dev`
- **Environment**: Production
- **Description**: FastAPI backend URL

### 3. NEXT_PUBLIC_DD_APPLICATION_ID
- **Value**: `goblin-assistant`
- **Environment**: Production
- **Description**: Datadog Application ID for frontend monitoring

### 4. NEXT_PUBLIC_DD_ENV
- **Value**: `production`
- **Environment**: Production
- **Description**: Datadog environment name

## How to Add Variables

1. Go to https://vercel.com/dashboard
2. Select your project (goblin-assistant or similar)
3. Go to **Settings** → **Environment Variables**
4. For each variable above:
   - Click **Add New**
   - Enter the variable name
   - Enter the value
   - Select **Production** environment
   - Click **Save**

## After Adding Variables

Once all variables are added, redeploy the application:

```bash
vercel deploy --prod
```

Or trigger a redeploy from the Vercel dashboard.

## Verify Deployment

Check your deployment URL (should be something like `https://goblin-assistant-*.vercel.app`) and verify the application is working correctly.
