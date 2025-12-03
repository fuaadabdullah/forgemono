#!/usr/bin/env bash
# Create and deploy project to a new Vercel team (Pro plan guidance)
set -euo pipefail

print_err() { echo "[ERROR] $*" >&2; }
print_info() { echo "[INFO] $*"; }
print_warn() { echo "[WARN] $*"; }

if ! command -v vercel >/dev/null 2>&1; then
  print_err "Vercel CLI is required. Install with: npm i -g vercel"
  exit 1
fi

if [ -z "${VERCEL_TOKEN:-}" ]; then
  print_warn "VERCEL_TOKEN is not set. For a fully non-interactive flow set VERCEL_TOKEN first."
fi

TEAM_NAME=${1:-}
if [ -z "$TEAM_NAME" ]; then
  read -r -p "Enter the new Vercel Team Name (e.g. 'My Team'): " TEAM_NAME
fi
if [ -z "$TEAM_NAME" ]; then
  print_err "Team name is required. Aborting."
  exit 1
fi

print_info "This script will:"
print_info "  1. Attempt to create a new Vercel team with the name: $TEAM_NAME (if your account allows it)"
print_info "  2. Link the current repo/project to that team"
print_info "  3. Deploy to the new team (prod)"
print_info "  4. Provide post-deploy checks and instructions to upgrade to the Pro plan via the Vercel web UI"

echo
print_info "Creating new team (if supported by your account)..."
if vercel teams create "$TEAM_NAME" --yes; then
  print_info "Team create command succeeded (if you saw an interactive prompt, follow it)."
else
  print_warn "Team creation may have failed or is interactive (e.g. insufficient permissions)." 
  print_warn "You can create a team manually in Vercel (Dashboard > Teams > New Team)."
fi

print_info "Switching to team: $TEAM_NAME"
if vercel switch --team "$TEAM_NAME"; then
  print_info "Switched to team $TEAM_NAME"
else
  print_warn "Could not switch to team via CLI. Use 'vercel switch' or create the team in the web UI then run 'vercel switch --team <team>'"
fi

print_info "Linking the current project to the team"
if vercel link --yes --confirm --team "$TEAM_NAME"; then
  print_info "Project linked to team $TEAM_NAME"
else
  print_warn "Auto-link failed. You can run 'vercel link --team $TEAM_NAME' manually from the project root to link it."
fi

print_info "Deploying the current project to the $TEAM_NAME team (production)"
if vercel --prod --yes --team "$TEAM_NAME"; then
  print_info "Deployment started — wait for finished status in the Vercel dashboard."
else
  print_warn "Deployment failed or was interactive. Please run: vercel --prod --team $TEAM_NAME and respond to prompts."
fi

cat <<EOF

Next steps (manual; required to increase serverless function quota):

1) Open the Vercel Dashboard: https://vercel.com/dashboard
2) From the top-left account menu, switch to the newly created Team: $TEAM_NAME
3) Go to the Team Settings > Billing
4) Add a payment method and upgrade the team to Pro (or higher) plan — the Hobby plan is limited to 12 Serverless Functions per deployment
5) Confirm the plan and billing; once upgraded your team will be allowed more Serverless Functions per project/deployment

Verification steps:
  - In Vercel Dashboard: Select the Team > Project > Settings > Functions and confirm the limits changed
  - Deploy again with the team scope: vercel --prod --team "$TEAM_NAME"
  - Check deployment logs in Vercel and confirm the functions deployed
  - Test production endpoints and confirm API calls succeed and that environment variables are intact

Security note:
  - Do not commit your VERCEL_TOKEN into version control; pass it via your CI environment or through your shell session when running the script

EOF

print_info "Done. If any step fails due to permission or billing limitations, create the team from the Vercel UI and upgrade the billing plan to Pro and re-run the link/deploy steps."

exit 0
