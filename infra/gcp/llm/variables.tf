variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "billing_account" {
  description = "Billing account ID to link the project to"
  type        = string
  default     = "01BA02-C7A6A7-4F4E25"
}

variable "region" {
  description = "GCP region for Cloud Run and networking"
  type        = string
  default     = "us-central1"
}

variable "zone" {
  description = "GCP zone for the llama GPU VM"
  type        = string
  default     = "us-central1-a"
}

variable "google_credentials_json" {
  description = "Optional JSON credentials for Terraform runs"
  type        = string
  default     = ""
  sensitive   = true
}

variable "create_network" {
  description = "Whether to create a dedicated VPC network"
  type        = bool
  default     = true
}

variable "network_name" {
  description = "Name of the VPC network (used when create_network=false)"
  type        = string
  default     = "llm-net"
}

variable "subnetwork_name" {
  description = "Name of the subnetwork (used when create_network=false)"
  type        = string
  default     = "llm-subnet"
}

variable "network_self_link" {
  description = "Existing VPC network self link (used when create_network=false)"
  type        = string
  default     = ""
}

variable "subnetwork_self_link" {
  description = "Existing subnetwork self link (used when create_network=false)"
  type        = string
  default     = ""
}

variable "subnet_cidr" {
  description = "CIDR block for the LLM subnetwork"
  type        = string
  default     = "10.70.0.0/20"
}

variable "vpc_connector_cidr" {
  description = "CIDR block for the Cloud Run VPC connector"
  type        = string
  default     = "10.70.16.0/28"
}

variable "ollama_allowed_cidrs" {
  description = "CIDR blocks allowed to reach llama on the VM"
  type        = list(string)
  default     = ["10.70.0.0/20"]
}

variable "enable_ollama_vm" {
  description = "Enable provisioning of the llama GPU VM"
  type        = bool
  default     = true
}

variable "ollama_vm_name" {
  description = "Name of the llama GPU VM"
  type        = string
  default     = "ollama-gpu"
}

variable "ollama_machine_type" {
  description = "Machine type for the llama VM"
  type        = string
  default     = "n1-standard-8"
}

variable "ollama_gpu_type" {
  description = "GPU type for the llama VM"
  type        = string
  default     = "nvidia-tesla-t4"
}

variable "ollama_gpu_count" {
  description = "Number of GPUs attached to the llama VM"
  type        = number
  default     = 1
}

variable "ollama_boot_disk_gb" {
  description = "Boot disk size in GB for the llama VM"
  type        = number
  default     = 200
}

variable "ollama_image_project" {
  description = "Image project for the llama VM"
  type        = string
  default     = "ubuntu-os-cloud"
}

variable "ollama_image_family" {
  description = "Image family for the llama VM"
  type        = string
  default     = "ubuntu-2204-lts"
}

variable "ollama_startup_script" {
  description = "Startup script for installing NVIDIA drivers and llama"
  type        = string
  default     = <<-EOT
    #!/usr/bin/env bash
    set -euo pipefail

    apt-get update -y
    apt-get install -y curl jq

    if ! command -v nvidia-smi >/dev/null 2>&1; then
      apt-get install -y ubuntu-drivers-common
      ubuntu-drivers install
    fi

    if ! command -v ollama >/dev/null 2>&1; then
      curl -fsSL https://ollama.com/install.sh | sh
    fi

    systemctl enable ollama
    systemctl restart ollama
  EOT
}

variable "create_service_account" {
  description = "Create a dedicated service account for the LLM services"
  type        = bool
  default     = true
}

variable "service_account_name" {
  description = "Service account name for LLM workloads"
  type        = string
  default     = "llm-runtime"
}

variable "ollama_service_account_email" {
  description = "Existing service account email for the llama VM"
  type        = string
  default     = ""
}

variable "enable_llamacpp_service" {
  description = "Enable Cloud Run llama.cpp service"
  type        = bool
  default     = true
}

variable "llamacpp_service_name" {
  description = "Cloud Run service name for llama.cpp"
  type        = string
  default     = "llamacpp"
}

variable "llamacpp_image" {
  description = "Container image for llama.cpp"
  type        = string
  default     = "ghcr.io/ggerganov/llama.cpp:server"
}

variable "llamacpp_container_port" {
  description = "Container port for llama.cpp"
  type        = number
  default     = 8080
}

variable "llamacpp_min_instances" {
  description = "Minimum instances for llama.cpp Cloud Run service"
  type        = number
  default     = 0
}

variable "llamacpp_max_instances" {
  description = "Maximum instances for llama.cpp Cloud Run service"
  type        = number
  default     = 2
}

variable "llamacpp_env" {
  description = "Environment variables for llama.cpp"
  type        = map(string)
  default = {
    MODEL_PATH = "/models/model.gguf"
  }
}

variable "enable_gateway_service" {
  description = "Enable Cloud Run model gateway service"
  type        = bool
  default     = true
}

variable "gateway_service_name" {
  description = "Cloud Run service name for the model gateway"
  type        = string
  default     = "model-gateway"
}

variable "gateway_image" {
  description = "Container image for the model gateway (local-llm-proxy)"
  type        = string
  default     = "ghcr.io/goblinos/local-llm-proxy:latest"
}

variable "gateway_container_port" {
  description = "Container port for the model gateway"
  type        = number
  default     = 8002
}

variable "gateway_min_instances" {
  description = "Minimum instances for the model gateway"
  type        = number
  default     = 1
}

variable "gateway_max_instances" {
  description = "Maximum instances for the model gateway"
  type        = number
  default     = 3
}

variable "gateway_env" {
  description = "Environment variables for the model gateway"
  type        = map(string)
  default     = {}
}

variable "cloud_run_ingress" {
  description = "Ingress setting for Cloud Run services"
  type        = string
  default     = "INGRESS_TRAFFIC_ALL"
}
