#!/bin/bash
set -e

# Bootstrap script for goblin-infra
# Run this to set up the Terraform state backend and CI credentials

echo "=== goblin-infra Bootstrap ==="
echo ""

# Check for required tools
command -v terraform >/dev/null 2>&1 || { echo "Error: terraform not found"; exit 1; }

# Determine which backend to use
echo "Which backend are you using?"
echo "1) Terraform Cloud (already configured)"
echo "2) AWS S3 + DynamoDB (needs setup)"
read -p "Enter choice [1]: " BACKEND_CHOICE
BACKEND_CHOICE=${BACKEND_CHOICE:-1}

if [ "$BACKEND_CHOICE" = "1" ]; then
    echo ""
    echo "=== Terraform Cloud Setup ==="
    echo ""
    echo "Your workspaces are already configured:"
    echo "  - GoblinOSAssistant (dev)"
    echo "  - GoblinOSAssistant-staging (staging)"
    echo "  - GoblinOSAssistant-prod (prod)"
    echo ""
    echo "Remaining steps:"
    echo "1. Go to GitHub repo settings → Environments"
    echo "2. Create 'staging' environment → Add 1 required reviewer"
    echo "3. Create 'production' environment → Add 2+ required reviewers"
    echo ""
    echo "Testing dev workspace..."
    cd ../envs/dev
    terraform init
    terraform plan
    echo ""
    echo "✅ Dev workspace is ready!"

elif [ "$BACKEND_CHOICE" = "2" ]; then
    echo ""
    echo "=== AWS S3 Backend Setup ==="
    echo ""

    # Check for AWS CLI
    command -v aws >/dev/null 2>&1 || { echo "Error: aws CLI not found"; exit 1; }

    echo "This will create:"
    echo "  - S3 bucket for Terraform state"
    echo "  - DynamoDB table for state locking"
    echo "  - IAM OIDC provider for GitHub Actions"
    echo "  - IAM role for CI"
    echo ""
    read -p "Continue? [y/N]: " CONFIRM

    if [ "$CONFIRM" = "y" ] || [ "$CONFIRM" = "Y" ]; then
        echo ""
        echo "Creating S3 backend..."
        terraform init
        terraform apply -target=aws_s3_bucket.tfstate -target=aws_s3_bucket_versioning.tfstate \
            -target=aws_s3_bucket_server_side_encryption_configuration.tfstate \
            -target=aws_s3_bucket_public_access_block.tfstate \
            -target=aws_dynamodb_table.tf_locks \
            -auto-approve

        echo ""
        echo "Creating GitHub OIDC provider and IAM role..."
        terraform apply -auto-approve

        echo ""
        echo "✅ Bootstrap complete!"
        echo ""
        echo "Next steps:"
        echo "1. Update envs/*/backend.tf with the S3 backend config"
        echo "2. Run 'terraform init' in each env directory"
        echo "3. Configure GitHub Environments with required reviewers"
    else
        echo "Cancelled."
    fi
else
    echo "Invalid choice."
    exit 1
fi

echo ""
echo "=== Bootstrap Complete ==="
