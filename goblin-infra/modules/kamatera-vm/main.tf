# Terraform module for provisioning a Kamatera VM with Goblin Assistant
# This is a template - adjust for your Kamatera provider setup

terraform {
  required_providers {
    kamatera = {
      source = "Kamatera/kamatera"
    }
  }
}

# Cloud-init user-data that bootstraps the VM
locals {
  cloud_init_user_data = templatefile("${path.module}/../../bootstrap/cloud-init.sh.tpl", {
    INSTANCE_ID = var.instance_name
  })
}

resource "kamatera_server" "vm" {
  name          = var.instance_name
  datacenter    = "EU" # Adjust as needed
  cpu_type      = "B"  # Budget CPU
  cpu_cores     = 2
  ram_mb        = 4096
  disk_sizes    = [20] # 20GB disk
  billing_cycle = "monthly"

  # Use Ubuntu 22.04
  image_id = "ubuntu_22.04_64-bit"

  # Network configuration
  network {
    name = "wan"
  }

  # Cloud-init user-data for bootstrap
  user_data = local.cloud_init_user_data

  # SSH key for access (replace with your key)
  ssh_key = file("~/.ssh/id_rsa.pub")

  # Power on after creation
  power_on = true
}

# Wait for cloud-init to complete
resource "null_resource" "wait_for_bootstrap" {
  depends_on = [kamatera_server.vm]

  provisioner "remote-exec" {
    connection {
      type        = "ssh"
      user        = "root"
      private_key = file("~/.ssh/id_rsa")
      host        = kamatera_server.vm.public_ip
    }

    inline = [
      "cloud-init status --wait",
      "systemctl is-active docker || exit 1"
    ]
  }
}
