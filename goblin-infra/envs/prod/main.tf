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
  default = "goblin-prod"
}

variable "env" {
  type    = string
  default = "prod"
}

resource "null_resource" "example" {
  provisioner "local-exec" {
    command = "echo provisioned ${var.name} in ${var.env}"
  }
}

output "example_msg" {
  value       = "example ${var.name} created in ${var.env}"
  description = "Prod example message"
}
