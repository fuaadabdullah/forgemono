variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "image_tag" {
  description = "Docker image tag to deploy"
  type        = string
}

variable "bootstrap_token" {
  description = "One-time bootstrap token for fetching secrets"
  type        = string
  sensitive   = true
}
