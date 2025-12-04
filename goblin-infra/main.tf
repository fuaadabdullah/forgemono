terraform {
  required_providers {
    kamatera = {
      source  = "Kamatera/kamatera"
      version = "~> 0.3"
    }
  }
}

# Use the Kamatera VM module
module "goblin_vm" {
  source = "./modules/kamatera-vm"

  instance_name   = "goblin-assistant-${var.environment}"
  image_tag       = var.image_tag
  bootstrap_token = var.bootstrap_token
}

# Outputs
output "vm_ip" {
  description = "VM public IP"
  value       = module.goblin_vm.instance_ip
}

output "instance_id" {
  description = "VM instance ID"
  value       = module.goblin_vm.instance_id
}

output "bootstrap_token" {
  description = "Bootstrap token (sensitive)"
  value       = module.goblin_vm.bootstrap_token
  sensitive   = true
}
