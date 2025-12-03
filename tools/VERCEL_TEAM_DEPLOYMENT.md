# Creating a Vercel Team and Deploying Projects (Pro plan)

This guide shows how to create a Vercel team, upgrade it to Pro, and move a project to that team for deployments that require more than 12 serverless functions.

Notes:
- Upgrading plan (Billing) must be done via the Vercel Dashboard. The CLI cannot complete the billing setup.
- You need a personal Vercel account or organization owner permissions to create a team and set billing.

1. Create a Vercel Team (via CLI or web):

CLI (recommended for automation):

```bash
# Optional: set a Vercel token in your environment (recommended for CI):
export VERCEL_TOKEN=your_token_here

# Create a new team
vercel teams create "My Team Name"

# Switch to the new team
vercel switch --team "My Team Name"
```

If you cannot create a team or want to confirm it via GUI, use the dashboard:

1. Go to https://vercel.com/dashboard
2. Click the account menu in the upper-left corner -> Create a Team
3. Enter Team name and create it

2. Upgrade the Team to Pro (billing)

1. In the Vercel Dashboard, switch to the new team
2. Go to Team Settings > Billing
3. Add a billing method (card) and choose Pro plan
4. Confirm and pay

3. Move or link project to the new Team

CLI link flow from the project root:

```bash
vercel link --team "My Team Name" --yes

# Or directly deploy to the team with:
vercel --prod --confirm --team "My Team Name"
```

Or in the Vercel UI:

1. Go to the project's settings page on the Vercel website
2. Use the 'Transfer' or 'Settings > General > Transfer Project' to move the project to the team

4. Ensure Environment Variables and Access

1. For the project in the Team, re-check environment variables in `Project > Settings > Environment Variables` to make sure `VITE_FASTAPI_URL`, `VITE_API_URL`, and other values are set
2. The CLI also allows `vercel env add` for adding environment variables for team-scoped projects

5. Deploying

From the project root, run:

```bash
vercel --prod --confirm --team "My Team Name"
```

This will trigger a team-level deployment using the Pro plan limits, allowing more serverless functions.

6. Verify serverless function limits and operations

From the Vercel Dashboard (Team):
1. Go to the Project > Settings > Functions to confirm function quotas and runtime
2. Deploy your app and check logs for successful upload of functions
3. Test endpoints and confirm behavior

7. Security and CI

- To script this flow in CI, set `VERCEL_TOKEN` as a secret and run the CLI commands in your CI pipeline
- Do not commit `VERCEL_TOKEN` to repo
- Use service accounts or deploy keys where possible if automations are required

Notes about limitations
- The CLI cannot perform plan/billing upgrades (this is a web-based flow requiring a payment method). The script provided in `tools/create-vercel-team-and-deploy.sh` assists with the team creation and link, but billing requires UI intervention.

Appendix: Useful Commands

```bash
# Show teams
vercel teams ls

# Add environment variable for the team project
vercel env add <NAME> <value> production --team "My Team Name"

# Deploy to team
vercel --prod --confirm --team "My Team Name"
```
