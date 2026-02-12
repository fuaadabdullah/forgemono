# Terraform Configuration for Multi-Provider LLM Infrastructure
#
# This module manages:
# - RunPod serverless endpoints
# - Vast.ai job automation (via CLI scripts)
# - GCS model storage buckets (Single region: us-east1 for alpha)
# - Secret management
#
# Region Strategy (Alpha Phase):
# - Single region: us-east1 (East Coast + RunPod proximity)
# - Multi-region is an optimization for later
# - Storage and deployment structured for easy region addition
#
# Usage:
#   terraform init
#   terraform plan -var-file="prod.tfvars"
#   terraform apply -var-file="prod.tfvars"

terraform {
  required_version = ">= 1.3.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    null = {
      source  = "hashicorp/null"
      version = "~> 3.2"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.5"
    }
  }

  backend "gcs" {
    bucket = "goblin-terraform-state"
    prefix = "llm-infra"
  }
}

# ==================== Variables ====================

variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region (single region for alpha phase)"
  type        = string
  default     = "us-east1" # East Coast + RunPod closest cluster
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "prod"
}

# RunPod Configuration
variable "runpod_api_key" {
  description = "RunPod API key"
  type        = string
  sensitive   = true
}

variable "runpod_endpoint_name" {
  description = "Name for RunPod serverless endpoint"
  type        = string
  default     = "goblin-inference"
}

# Vast.ai Configuration
variable "vastai_api_key" {
  description = "Vast.ai API key"
  type        = string
  sensitive   = true
}

# Model Storage Configuration
variable "model_bucket_name" {
  description = "GCS bucket for model weights"
  type        = string
  default     = "goblin-llm-models"
}

variable "checkpoint_bucket_name" {
  description = "GCS bucket for training checkpoints"
  type        = string
  default     = "goblin-llm-checkpoints"
}

variable "model_encryption_key" {
  description = "Encryption key for sensitive model weights"
  type        = string
  sensitive   = true
  default     = ""
}

# ==================== Provider Configuration ====================

provider "google" {
  project = var.project_id
  region  = var.region
}

# ==================== GCS Buckets ====================

resource "google_storage_bucket" "models" {
  name          = "${var.model_bucket_name}-${var.environment}"
  location      = var.region
  force_destroy = false

  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }

  lifecycle_rule {
    condition {
      num_newer_versions = 5
    }
    action {
      type = "Delete"
    }
  }

  # Encryption at rest
  encryption {
    default_kms_key_name = var.model_encryption_key != "" ? google_kms_crypto_key.model_key[0].id : null
  }

  labels = {
    environment = var.environment
    purpose     = "llm-models"
  }
}

resource "google_storage_bucket" "checkpoints" {
  name          = "${var.checkpoint_bucket_name}-${var.environment}"
  location      = var.region
  force_destroy = false

  uniform_bucket_level_access = true

  versioning {
    enabled = false
  }

  # Auto-delete old checkpoints
  lifecycle_rule {
    condition {
      age = 30 # days
    }
    action {
      type = "Delete"
    }
  }

  labels = {
    environment = var.environment
    purpose     = "training-checkpoints"
  }
}

# ==================== KMS for Encryption ====================

resource "google_kms_key_ring" "llm" {
  count    = var.model_encryption_key != "" ? 1 : 0
  name     = "goblin-llm-keyring-${var.environment}"
  location = var.region
}

resource "google_kms_crypto_key" "model_key" {
  count    = var.model_encryption_key != "" ? 1 : 0
  name     = "model-encryption-key"
  key_ring = google_kms_key_ring.llm[0].id

  lifecycle {
    prevent_destroy = true
  }
}

# ==================== Service Account ====================

resource "google_service_account" "llm_service" {
  account_id   = "goblin-llm-service-${var.environment}"
  display_name = "Goblin LLM Service Account"
}

resource "google_storage_bucket_iam_member" "model_access" {
  bucket = google_storage_bucket.models.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.llm_service.email}"
}

resource "google_storage_bucket_iam_member" "checkpoint_access" {
  bucket = google_storage_bucket.checkpoints.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.llm_service.email}"
}

resource "google_service_account_key" "llm_service_key" {
  service_account_id = google_service_account.llm_service.name
}

# ==================== Secret Manager ====================

resource "google_secret_manager_secret" "runpod_api_key" {
  secret_id = "runpod-api-key-${var.environment}"

  replication {
    auto {}
  }

  labels = {
    environment = var.environment
    provider    = "runpod"
  }
}

resource "google_secret_manager_secret_version" "runpod_api_key" {
  secret      = google_secret_manager_secret.runpod_api_key.id
  secret_data = var.runpod_api_key
}

resource "google_secret_manager_secret" "vastai_api_key" {
  secret_id = "vastai-api-key-${var.environment}"

  replication {
    auto {}
  }

  labels = {
    environment = var.environment
    provider    = "vastai"
  }
}

resource "google_secret_manager_secret_version" "vastai_api_key" {
  secret      = google_secret_manager_secret.vastai_api_key.id
  secret_data = var.vastai_api_key
}

# ==================== RunPod Endpoint Management ====================

# RunPod doesn't have a Terraform provider, so we use local-exec
# This creates the endpoint configuration file that can be used with the RunPod CLI/API

resource "local_file" "runpod_config" {
  filename = "${path.module}/generated/runpod-config.json"
  content = jsonencode({
    endpoint_name = var.runpod_endpoint_name
    environment   = var.environment
    config = {
      gpu_types    = ["NVIDIA A100 80GB", "NVIDIA H100 80GB"]
      min_workers  = 0
      max_workers  = 5
      idle_timeout = 60
      scale_type   = "QUEUE_DELAY"
      flash_boot   = true
    }
    model_storage = {
      bucket = google_storage_bucket.models.name
      prefix = "models/"
    }
  })
}

# Script to deploy RunPod endpoint
resource "null_resource" "runpod_endpoint" {
  depends_on = [local_file.runpod_config]

  triggers = {
    config_hash = sha256(local_file.runpod_config.content)
  }

  provisioner "local-exec" {
    command = <<-EOT
      echo "RunPod endpoint configuration generated."
      echo "To deploy, run: ./scripts/deploy_runpod_endpoint.sh"
      echo "Config file: ${local_file.runpod_config.filename}"
    EOT
  }
}

# ==================== Vast.ai Automation Scripts ====================

resource "local_file" "vastai_config" {
  filename = "${path.module}/generated/vastai-config.json"
  content = jsonencode({
    environment = var.environment
    search_criteria = {
      min_reliability    = 0.95
      min_dlperf         = 10.0
      min_internet_speed = 100
      preferred_regions  = ["us", "eu"]
      preferred_gpus     = ["RTX 4090", "A100 80GB", "H100 80GB"]
    }
    job_defaults = {
      checkpoint_interval_minutes = 30
      checkpoint_bucket           = google_storage_bucket.checkpoints.name
      model_bucket                = google_storage_bucket.models.name
      encrypt_weights             = true
    }
  })
}

# ==================== Outputs ====================

output "model_bucket" {
  description = "GCS bucket for model weights"
  value       = google_storage_bucket.models.name
}

output "checkpoint_bucket" {
  description = "GCS bucket for checkpoints"
  value       = google_storage_bucket.checkpoints.name
}

output "service_account_email" {
  description = "Service account for LLM services"
  value       = google_service_account.llm_service.email
}

output "service_account_key" {
  description = "Service account key (base64 encoded)"
  value       = google_service_account_key.llm_service_key.private_key
  sensitive   = true
}

output "runpod_secret_name" {
  description = "Secret Manager secret for RunPod API key"
  value       = google_secret_manager_secret.runpod_api_key.name
}

output "vastai_secret_name" {
  description = "Secret Manager secret for Vast.ai API key"
  value       = google_secret_manager_secret.vastai_api_key.name
}

output "runpod_config_path" {
  description = "Path to generated RunPod configuration"
  value       = local_file.runpod_config.filename
}

output "vastai_config_path" {
  description = "Path to generated Vast.ai configuration"
  value       = local_file.vastai_config.filename
}
