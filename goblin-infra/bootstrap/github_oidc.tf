# GitHub Actions OIDC Provider and IAM Role for AWS
# Run this after creating the S3 backend to set up CI credentials

terraform {
  required_version = ">= 1.4.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.0.0"
    }
  }
}

variable "region" {
  type        = string
  default     = "us-east-1"
  description = "AWS region"
}

variable "github_org" {
  type        = string
  default     = "fuaadabdullah"
  description = "GitHub organization or username"
}

variable "github_repo" {
  type        = string
  default     = "forgemono"
  description = "GitHub repository name"
}

variable "state_bucket_arn" {
  type        = string
  default     = "arn:aws:s3:::goblin-terraform-state"
  description = "ARN of the S3 bucket for Terraform state"
}

variable "lock_table_arn" {
  type        = string
  default     = "arn:aws:dynamodb:us-east-1:YOUR_AWS_ACCOUNT_ID:table/goblin-terraform-locks"
  description = "ARN of the DynamoDB table for state locking"
}

provider "aws" {
  region = var.region
}

# Get current AWS account ID
data "aws_caller_identity" "current" {}

# OIDC Provider for GitHub Actions
resource "aws_iam_openid_connect_provider" "github" {
  url = "https://token.actions.githubusercontent.com"

  client_id_list = ["sts.amazonaws.com"]

  thumbprint_list = [
    "6938fd4d98bab03faadb97b34396831e3780aea1",
    "1c58a3a8518e8759bf075b76b750d4f2df264fcd"
  ]

  tags = {
    Name      = "GitHub Actions OIDC"
    ManagedBy = "terraform-bootstrap"
  }
}

# IAM Role for GitHub Actions
resource "aws_iam_role" "github_actions" {
  name = "GitHubActionsTerraformRole"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Federated = aws_iam_openid_connect_provider.github.arn
        }
        Action = "sts:AssumeRoleWithWebIdentity"
        Condition = {
          StringEquals = {
            "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com"
          }
          StringLike = {
            "token.actions.githubusercontent.com:sub" = "repo:${var.github_org}/${var.github_repo}:*"
          }
        }
      }
    ]
  })

  tags = {
    Name      = "GitHub Actions Terraform Role"
    ManagedBy = "terraform-bootstrap"
  }
}

# IAM Policy for Terraform state access
resource "aws_iam_role_policy" "terraform_state" {
  name = "TerraformStateAccess"
  role = aws_iam_role.github_actions.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "S3StateAccess"
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket",
          "s3:GetBucketLocation"
        ]
        Resource = [
          var.state_bucket_arn,
          "${var.state_bucket_arn}/*"
        ]
      },
      {
        Sid    = "DynamoDBLockAccess"
        Effect = "Allow"
        Action = [
          "dynamodb:PutItem",
          "dynamodb:GetItem",
          "dynamodb:DeleteItem",
          "dynamodb:DescribeTable"
        ]
        Resource = var.lock_table_arn
      },
      {
        Sid    = "KMSAccess"
        Effect = "Allow"
        Action = [
          "kms:Decrypt",
          "kms:Encrypt",
          "kms:GenerateDataKey"
        ]
        Resource = "*"
        Condition = {
          StringEquals = {
            "kms:ViaService" = "s3.${var.region}.amazonaws.com"
          }
        }
      }
    ]
  })
}

# Outputs
output "role_arn" {
  value       = aws_iam_role.github_actions.arn
  description = "IAM Role ARN for GitHub Actions"
}

output "oidc_provider_arn" {
  value       = aws_iam_openid_connect_provider.github.arn
  description = "OIDC Provider ARN"
}

output "github_actions_config" {
  value = <<-EOT
    # Add this to your GitHub Actions workflow:

    permissions:
      id-token: write
      contents: read

    steps:
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${aws_iam_role.github_actions.arn}
          aws-region: ${var.region}
  EOT
  description = "GitHub Actions configuration snippet"
}
