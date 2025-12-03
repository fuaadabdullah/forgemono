# Prod-specific variables
# Add production-grade inputs here (region, instance sizes, multi-AZ, encryption keys, etc.)

variable "region" {
  type        = string
  default     = "us-east-1"
  description = "AWS region for prod resources"
}
