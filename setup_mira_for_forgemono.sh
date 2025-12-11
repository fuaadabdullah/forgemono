#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

# ----------------------------
# CONFIG - fill these before run
# ----------------------------
GITHUB_REPO="${GITHUB_REPO:-fuaadabdullah/forgemono}"
GITHUB_HANDLE="${GITHUB_HANDLE:-@fuaadabdullah}"

# Mandatory manual Jira token creation (Atlassian UI)
JIRA_SITE="${JIRA_SITE:-your-domain.atlassian.net}"       # e.g., fuaad.atlassian.net
JIRA_EMAIL="${JIRA_EMAIL:-forgemono-mira@yourdomain.com}" # your Jira service account email
JIRA_TOKEN="${JIRA_TOKEN:-}" # MUST EXPORT before running or echo will fail

# Mira: you must create this in Mira admin dashboard (or ask Mira admin)
MIRA_API_URL="${MIRA_API_URL:-https://api.mira.co}"  # change if self-hosted
MIRA_TOKEN="${MIRA_TOKEN:-}" # create via Mira UI

# Optional CI / infra secrets
CLOUDFLARE_API_TOKEN="${CLOUDFLARE_API_TOKEN:-}"
CIRCLECI_TOKEN="${CIRCLECI_TOKEN:-}"

# GitHub App / webhook details (if Mira gave you a webhook)
GITHUB_APP_WEBHOOK_URL="${GITHUB_APP_WEBHOOK_URL:-https://hooks.mira.co/forgemono/webhook}"

# Jira Key regex used by workflows
JIRA_REGEX="${JIRA_REGEX:-PROJ-\\d+}"

# Branch protection checks' names (update to actual workflow names if different)
STATUS_CHECKS=("unit-tests" "lint" "require-jira")

# ----------------------------
# sanity
# ----------------------------
if [[ -z "${JIRA_TOKEN}" ]]; then
  echo "ERROR: JIRA_TOKEN is empty. Create a Jira API token manually and export JIRA_TOKEN env var."
  echo "See https://id.atlassian.com/manage-profile/security/api-tokens"
  exit 1
fi

if [[ -z "${MIRA_TOKEN}" ]]; then
  echo "WARNING: MIRA_TOKEN is empty. You can still generate repo files and GH secrets, but Mira will not be configured."
fi

echo "Running setup for GitHub repo: $GITHUB_REPO"
REPO_NAME=$(echo "$GITHUB_REPO" | cut -d/ -f2)
TMP_DIR=$(mktemp -d /tmp/forge-setup.XXXX)
echo "temp dir: $TMP_DIR"

# ----------------------------
# 1) create repo branch, add CODEOWNERS, PR template, GH action
# ----------------------------
cat > "$TMP_DIR/CODEOWNERS" <<EOF
# CODEOWNERS for forgemono
/goblin-infra/ @${GITHUB_HANDLE#@}
/goblin-assistant/ @${GITHUB_HANDLE#@}
/apps/forge-lite/ @${GITHUB_HANDLE#@}
/apps/raptor-mini/ @${GITHUB_HANDLE#@}
/goblin-assistant-contracts/ @${GITHUB_HANDLE#@}
/chroma_db/ @${GITHUB_HANDLE#@}
/vector_db/ @${GITHUB_HANDLE#@}
* @${GITHUB_HANDLE#@}
EOF

mkdir -p "$TMP_DIR/.github"
cat > "$TMP_DIR/.github/PULL_REQUEST_TEMPLATE.md" <<'EOF'
## Summary
Short summary of the change (1-2 lines)

## Jira ticket
Related ticket (required): PROJ-123

## Testing
- Unit tests: pass/fail
- Integration tests: pass/fail
- Local validation steps:

## Deployment
- Infra change? yes/no
- Migration required? yes/no
- Rollback plan:

## Checklist
- [ ] Jira ticket linked in title or branch name
- [ ] CODEOWNERS assigned reviewer(s)
- [ ] Tests passing
- [ ] Deployment impact documented
EOF

mkdir -p "$TMP_DIR/.github/workflows"
cat > "$TMP_DIR/.github/workflows/require-jira-key.yml" <<EOF
name: Require-Jira-Key
on:
  pull_request_target:
    types: [opened, edited, reopened, synchronize]

permissions:
  checks: read
  pull-requests: write
  contents: read

jobs:
  require-jira:
    runs-on: ubuntu-latest
    steps:
      - name: Check PR title or branch for Jira key
        run: |
          set -e
          KEY_REGEX='${JIRA_REGEX}'
          PR_TITLE="\${{ github.event.pull_request.title }}"
          BRANCH_NAME="\${{ github.event.pull_request.head_ref }}"
          BODY="\${{ github.event.pull_request.body }}"
          echo "PR title: \$PR_TITLE"
          echo "Branch name: \$BRANCH_NAME"

          if echo "\$PR_TITLE" | grep -Eiq "\$KEY_REGEX" || echo "\$BRANCH_NAME" | grep -Eiq "\$KEY_REGEX" || echo "\$BODY" | grep -Eiq "\$KEY_REGEX"; then
            echo "Jira key detected"
            exit 0
          else
            echo "No Jira key found in PR title, branch name, or body." >&2
            echo "Please include a Jira issue key (eg. PROJ-123) in the PR title or branch name." >&2
            exit 1
          fi
EOF

# commit files into a feature branch and open a PR
pushd "$TMP_DIR" >/dev/null
git init -q
git checkout -b chore/add-ci-templates
git config user.email "github-actions[bot]@users.noreply.github.com"
git config user.name "github-actions[bot]"
git add .
git commit -m "chore(ci): add CODEOWNERS, PR template, require-jira-key workflow"
# add remote and push
git remote add origin "git@github.com:${GITHUB_REPO}.git"
echo "Pushing branch to origin..."
git push -u origin chore/add-ci-templates
popd >/dev/null

# create PR using gh
echo "Creating PR..."
gh pr create --repo "$GITHUB_REPO" --title "chore: add CI templates (PROJ-000)" --body "Adds CODEOWNERS, PR template and require-jira-key workflow." --base main --head chore/add-ci-templates || true

# ----------------------------
# 2) create GitHub repo secrets (use gh secret)
# ----------------------------
echo "Adding repo secrets (github)."
# helper to set secret (uses gh secret)
function gh_set_secret {
  local name="$1"; shift
  local value="$1"; shift
  if [[ -z "${value}" ]]; then
    echo "Skipping secret $name - empty."
    return
  fi
  echo -n "$value" | gh secret set "$name" --repo "$GITHUB_REPO"
  echo "Set secret $name"
}

gh_set_secret "JIRA_SITE" "$JIRA_SITE"
gh_set_secret "JIRA_EMAIL" "$JIRA_EMAIL"
gh_set_secret "JIRA_TOKEN" "$JIRA_TOKEN"
gh_set_secret "MIRA_API_URL" "$MIRA_API_URL"
gh_set_secret "MIRA_TOKEN" "$MIRA_TOKEN"
gh_set_secret "CLOUDFLARE_API_TOKEN" "$CLOUDFLARE_API_TOKEN"
gh_set_secret "CIRCLECI_TOKEN" "$CIRCLECI_TOKEN"

# ----------------------------
# 3) Create GitHub webhook to Mira (optional)
# ----------------------------
if [[ -n "${GITHUB_APP_WEBHOOK_URL}" ]]; then
  echo "Creating repo webhook to $GITHUB_APP_WEBHOOK_URL"
  gh api --method POST -H "Accept: application/vnd.github+json" \
    -f "config={\"url\":\"${GITHUB_APP_WEBHOOK_URL}\",\"content_type\":\"json\"}" \
    -f "events=['pull_request','push','status','check_run']" \
    "/repos/${GITHUB_REPO}/hooks" >/dev/null
  echo "Webhook created."
else
  echo "No GITHUB_APP_WEBHOOK_URL provided. Skipping webhook creation."
fi

# ----------------------------
# 4) Apply branch protection to main
# ----------------------------
# Build contexts array for status checks
contexts_json=$(jq -n --argjson arr "$(printf '%s\n' "${STATUS_CHECKS[@]}" | jq -R . | jq -s .)" '$arr')
echo "Applying branch protection to main with required status checks: ${STATUS_CHECKS[*]}"
gh api repos/"$GITHUB_REPO"/branches/main/protection -X PUT -f required_status_checks="$(jq -n --argjson contexts "$contexts_json" '{"strict":true,"contexts":$contexts}' )" -f required_pull_request_reviews='{"required_approving_review_count":1}' -f enforce_admins=true || echo "Branch protection API returned non-zero, you may need admin rights."

# ----------------------------
# 5) Test Jira auth and Mira ping (curl tests)
# ----------------------------
echo "Testing Jira auth..."
curl -s -u "${JIRA_EMAIL}:${JIRA_TOKEN}" -H "Accept: application/json" "https://${JIRA_SITE}/rest/api/3/myself" | jq . || echo "Jira test: non-200 or jq not installed"

if [[ -n "${MIRA_TOKEN}" ]]; then
  echo "Testing Mira ping..."
  curl -s -i -H "Authorization: Bearer ${MIRA_TOKEN}" "${MIRA_API_URL%/}/v1/linker/ping" || echo "Mira ping failed (maybe endpoint differs)."
fi

# ----------------------------
# 6) Optional: create sample CircleCI terraform plan job stub file in repo
# ----------------------------
cat > "$TMP_DIR/.circleci-config-sample.yml" <<'EOF'
# sample CircleCI job for infra/tf plan
version: 2.1
jobs:
  tf-plan:
    docker:
      - hashicorp/terraform:1.5
    steps:
      - checkout
      - run: terraform init
      - run: terraform fmt -check
      - run: terraform validate
      - run: tfsec .
      - run: terraform plan -out=tfplan
      - store_artifacts:
          path: tfplan
EOF

echo "Wrote sample CircleCI tf-plan stub to $TMP_DIR/.circleci-config-sample.yml (inspect and move into repo if wanted)."

echo "DONE. A PR with changes has been created. GitHub secrets set (where provided)."
echo "Next manual steps:"
echo " 1) Manually create Jira API token (Atlassian UI) and paste into the repo secret JIRA_TOKEN if you didn't already."
echo " 2) In Mira admin, add GitHub integration and Jira integration and point Mira webhook URL (or use the webhook we created) to Mira endpoint."
echo " 3) Verify webhooks & test PR/branch flow: open a branch 'feature/PROJ-123-test' and a PR to see the GH Action run."

exit 0
