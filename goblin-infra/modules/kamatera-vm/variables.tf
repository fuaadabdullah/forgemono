variable "instance_name" {
  description = "Name of the VM instance"
  type        = string
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

variable "instance_type" {
  description = "Kamatera instance type"
  type        = string
  default     = "kamatera-vm"
}

# Outputs
output "instance_ip" {
  description = "Public IP of the VM"
  value       = kamatera_server.vm.public_ip
}

output "instance_id" {
  description = "Unique instance identifier"
  value       = kamatera_server.vm.id
}

output "bootstrap_token" {
  description = "Bootstrap token for secret fetching"
  value       = var.bootstrap_token
  sensitive   = true
}
