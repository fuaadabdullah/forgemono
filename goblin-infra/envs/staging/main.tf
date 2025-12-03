terraform {
  required_version = ">= 1.4.0"
  required_providers {
    null = {
      source  = "hashicorp/null"
      version = ">= 3.0.0"
    }
  }
}

provider "null" {}

variable "name" {
  type    = string
  default = "goblin-staging"
}

resource "null_resource" "example" {
  provisioner "local-exec" {
    command = "echo provisioned ${var.name}"
  }
}

output "example_msg" {
  value       = "example ${var.name} created"
  description = "example staging message"
}
