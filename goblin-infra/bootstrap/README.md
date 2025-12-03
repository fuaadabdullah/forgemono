# Bootstrap — goblin-infra

This directory contains bootstrap resources for setting up Terraform state backends and CI credentials.

## Current Setup: HCP Terraform Cloud

You're using HCP Terraform Cloud (org: `GoblinOS`) with workspaces:

| Environment | Workspace |
|-------------|-----------|
| dev | `GoblinOSAssistant` |
| staging | `GoblinOSAssistant-staging` |
| prod | `GoblinOSAssistant-prod` |

### What's Already Done

- ✅ Terraform Cloud org created
- ✅ Workspaces created for dev/staging/prod
- ✅ CLI authentication (`terraform login`)
- ✅ Backend configs in `envs/*/backend.tf`

### Remaining Steps

1. **GitHub Environment Protection** (in GitHub repo settings):
   - Create `staging` environment → Add 1 required reviewer
   - Create `production` environment → Add 2+ required reviewers

2. **Optional: Add TFC_TOKEN to GitHub secrets** (only if you need API access):
   ```
   Settings → Secrets → Actions → New repository secret
   Name: TFC_TOKEN
   Value: <your terraform cloud token>
   ```

3. **Test the setup**:
   ```bash
   cd envs/dev && terraform init && terraform plan
   ```

---

## Alternative: AWS S3 Backend Bootstrap

If you ever need to self-host state in AWS S3 + DynamoDB, use the files in this directory.

### Quick Setup (AWS CLI)

```bash
# Set your values
export AWS_REGION=us-east-1
export BUCKET=goblin-terraform-state-$(date +%s)

# Create S3 bucket with versioning and encryption
aws s3api create-bucket --bucket $BUCKET --region $AWS_REGION
aws s3api put-bucket-versioning --bucket $BUCKET --versioning-configuration Status=Enabled
aws s3api put-bucket-encryption --bucket $BUCKET --server-side-encryption-configuration '{
  "Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"}}]
}'

# Create DynamoDB lock table
aws dynamodb create-table \
  --table-name goblin-terraform-locks \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region $AWS_REGION
```

### Or Use Terraform

```bash
cd bootstrap
terraform init
terraform apply -auto-approve
```

Then update your `envs/*/backend.tf` files to use the S3 backend instead of Terraform Cloud.

---

## GitHub Actions OIDC (AWS)

If using AWS, set up OIDC trust so GitHub Actions can assume a role without long-lived secrets.

### 1. Create OIDC Provider (one-time)

```bash
aws iam create-open-id-connect-provider \
  --url https://token.actions.githubusercontent.com \
  --client-id-list sts.amazonaws.com \
  --thumbprint-list 6938fd4d98bab03faadb97b34396831e3780aea1
```

### 2. Create IAM Role

```bash
# Edit trust.json with your AWS account ID and GitHub repo
aws iam create-role \
  --role-name GitHubActionsTerraformRole \
  --assume-role-policy-document file://trust.json

aws iam put-role-policy \
  --role-name GitHubActionsTerraformRole \
  --policy-name TerraformStateAccess \
  --policy-document file://policy.json
```

### 3. Update GitHub Actions

Add to your workflow:

```yaml
permissions:
  id-token: write
  contents: read

steps:
  - name: Configure AWS credentials
    uses: aws-actions/configure-aws-credentials@v4
    with:
      role-to-assume: arn:aws:iam::YOUR_ACCOUNT_ID:role/GitHubActionsTerraformRole
      aws-region: us-east-1
```

---

## Checklist

- [ ] Remote state backend created & reachable
- [ ] CI trust and credentials configured (TFC token or AWS OIDC)
- [ ] GitHub Environments created with required reviewers
- [ ] Smoke test scripts ready
- [ ] KMS encryption configured (optional but recommended)
- [ ] Monitoring/alerting hooks set up
