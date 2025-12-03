# Bootstrap Terraform for AWS S3 + DynamoDB state backend
# Run this ONCE with admin credentials to create the state backend
# Do NOT use a remote backend for this bootstrap — use local state

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
  description = "AWS region for state backend"
}

variable "bucket_name" {
  type        = string
  default     = "goblin-terraform-state"
  description = "S3 bucket name for Terraform state"
}

variable "dynamodb_table_name" {
  type        = string
  default     = "goblin-terraform-locks"
  description = "DynamoDB table name for state locking"
}

provider "aws" {
  region = var.region
}

# S3 bucket for Terraform state
resource "aws_s3_bucket" "tfstate" {
  bucket = var.bucket_name

  tags = {
    Name        = "Terraform State"
    Environment = "shared"
    ManagedBy   = "terraform-bootstrap"
  }
}

resource "aws_s3_bucket_versioning" "tfstate" {
  bucket = aws_s3_bucket.tfstate.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "tfstate" {
  bucket = aws_s3_bucket.tfstate.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "tfstate" {
  bucket = aws_s3_bucket.tfstate.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# DynamoDB table for state locking
resource "aws_dynamodb_table" "tf_locks" {
  name         = var.dynamodb_table_name
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "LockID"

  attribute {
    name = "LockID"
    type = "S"
  }

  tags = {
    Name        = "Terraform State Locks"
    Environment = "shared"
    ManagedBy   = "terraform-bootstrap"
  }
}

# Outputs
output "s3_bucket_name" {
  value       = aws_s3_bucket.tfstate.id
  description = "S3 bucket name for Terraform state"
}

output "s3_bucket_arn" {
  value       = aws_s3_bucket.tfstate.arn
  description = "S3 bucket ARN"
}

output "dynamodb_table_name" {
  value       = aws_dynamodb_table.tf_locks.name
  description = "DynamoDB table name for state locking"
}

output "dynamodb_table_arn" {
  value       = aws_dynamodb_table.tf_locks.arn
  description = "DynamoDB table ARN"
}

output "backend_config" {
  value = <<-EOT
    # Add this to your envs/*/backend.tf files:
    terraform {
      backend "s3" {
        bucket         = "${aws_s3_bucket.tfstate.id}"
        key            = "envs/<ENV>/terraform.tfstate"
        region         = "${var.region}"
        dynamodb_table = "${aws_dynamodb_table.tf_locks.name}"
        encrypt        = true
      }
    }
  EOT
  description = "Backend configuration to use in envs"
}
