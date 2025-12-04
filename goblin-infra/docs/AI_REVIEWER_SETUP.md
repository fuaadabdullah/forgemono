# AI Reviewer & Automation Setup

This document describes the AI-powered review and approval automation for goblin-infra.

## Overview

| Environment | Automation Level | Approvers |
|-------------|------------------|-----------|
| **Dev** | Full auto-approve | AI Bot |
| **Staging** | AI review + 1-click human approval | AI Bot + 1 human |
| **Prod** | AI review + human approval | 1 AI agent + 1 human |

## Workflows

### PR IaC Checks (`pr-iac-checks.yml`)
Runs on all PRs:
- Terraform fmt, validate
- tfsec security scan
- Checkov compliance scan

### Auto-Approve Dev (`auto-approve-dev.yml`)
- Triggers: PRs with `auto-approve-dev` label affecting `envs/dev/`
- Action: AI bot automatically approves after checks pass
- Auto-merge: Optional, enabled with `auto-merge` label

### Staging Approval Bot (`staging-approval-bot.yml`)
- Triggers: PRs with `staging-review` label affecting `envs/staging/`
- Action: AI bot posts review summary, requests human approval
- Human clicks approve, then merge

### Prod Approval Bot (`prod-approval-bot.yml`)
- Triggers: All PRs affecting `envs/prod/`
- Action: AI agent posts risk assessment and plan summary
- **NO auto-approve** - requires 1 human reviewer after AI review

### Cost Estimate (`cost-estimate.yml`)

- Triggers: All PRs affecting infrastructure
- Action: Posts cost estimate comment
- Requires `INFRACOST_API_KEY` secret (optional)

## Labels

| Label | Purpose |
|-------|---------|
| `auto-approve-dev` | Enable auto-approval for dev PRs |
| `staging-review` | Trigger AI staging review |
| `prod-review-required` | Auto-added to prod PRs |
| `no-auto-approve` | Block auto-approval |
| `awaiting-human-approval` | AI reviewed, needs human |
| `auto-merge` | Auto-merge after approval |

## Setup Checklist

### 1. GitHub Environment Protection

- [ ] Create `staging` environment → Add 1 required reviewer
- [ ] Create `production` environment → Add 1 required reviewer

### 2. Bot Account (Optional)

- [ ] Create bot GitHub account or GitHub App
- [ ] Add to repo with `pull_requests` permission
- [ ] Add `BOT_TOKEN` as org/repo secret

### 3. Branch Protection

- [ ] Require status checks: `PR IaC Checks`
- [ ] Require approvals: 1 for staging, 1 for prod
- [ ] Enable auto-merge (optional, dev only)

### 4. Secrets

- [ ] `BOT_TOKEN` - Bot account PAT (optional)
- [ ] `INFRACOST_API_KEY` - Cost estimation (optional)
- [ ] `TFC_TOKEN` - Terraform Cloud (if needed)

## Security Rules

1. **Dev**: Bot can approve and auto-merge
2. **Staging**: Bot suggests approval, human clicks approve
3. **Prod**: NO bot approvals. Bot prepares summary only.

## Cost Thresholds

If cost estimate exceeds threshold, auto-approve is blocked:

- Dev: No threshold
- Staging: >$100/month triggers review
- Prod: >$500/month requires additional approval

## Audit Trail

All bot actions are logged:

- GitHub PR comments show AI reviewer decisions
- Bot account actions visible in audit log
- Filter by actor to see all bot approvals
