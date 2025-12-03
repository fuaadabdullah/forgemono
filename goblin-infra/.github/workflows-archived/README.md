# GitHub Actions Archived

These workflows have been archived after migrating to **CircleCI**.

## Why CircleCI?

- **Lower maintenance** - No Jenkins-style sysadmin chores
- **Better free tier** - Useful credits for solo dev
- **Easy Docker builds** - Native parallelism and caching
- **Cleaner UX** - Simpler than GitHub Actions for complex pipelines

## Archived Workflows

| Workflow | Original Purpose |
|----------|------------------|
| `terraform-plan.yml` | Run terraform plan on PRs |
| `terraform-apply-dev.yml` | Auto-apply to dev on merge |
| `terraform-plan-staging.yml` | Plan for staging env |
| `terraform-apply-staging.yml` | Manual apply to staging |
| `terraform-plan-prod.yml` | Plan for prod env |
| `terraform-apply-prod.yml` | Manual apply to prod |
| `pr-iac-checks.yml` | tfsec/checkov security scans |
| `auto-approve-dev.yml` | Auto-approve dev PRs |
| `staging-approval-bot.yml` | Bot approval for staging |
| `prod-approval-bot.yml` | Bot approval for prod |
| `cost-estimate.yml` | Infracost estimates |

## New CI/CD Location

All CI/CD is now handled by CircleCI:

```
ForgeMonorepo/.circleci/
├── config.yml    # Main pipeline config
└── SETUP.md      # Setup documentation
```

## Restoring GitHub Actions

If you need to switch back:

```bash
mv .github/workflows-archived/*.yml .github/workflows/
```

---

**Archived**: December 3, 2025
