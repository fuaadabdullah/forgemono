locals {
  enable_vpc_connector = var.enable_llamacpp_service || var.enable_gateway_service
  network_name         = var.create_network ? google_compute_network.llm[0].name : var.network_name
  network_self_link    = var.create_network ? google_compute_network.llm[0].self_link : var.network_self_link
  subnetwork_name      = var.create_network ? google_compute_subnetwork.llm[0].name : var.subnetwork_name
  subnetwork_self_link = var.create_network ? google_compute_subnetwork.llm[0].self_link : var.subnetwork_self_link
  service_account_email = var.create_service_account ? google_service_account.llm[0].email : (
    var.ollama_service_account_email != "" ? var.ollama_service_account_email : null
  )
}

resource "google_project" "llm" {
  name            = "Goblin Assistant LLM"
  project_id      = var.project_id
  billing_account = var.billing_account
}

resource "google_compute_network" "llm" {
  count                   = var.create_network ? 1 : 0
  name                    = var.network_name
  auto_create_subnetworks = false
}

resource "google_compute_subnetwork" "llm" {
  count         = var.create_network ? 1 : 0
  name          = var.subnetwork_name
  ip_cidr_range = var.subnet_cidr
  region        = var.region
  network       = google_compute_network.llm[0].self_link
}

resource "google_compute_firewall" "ollama_allow" {
  count   = var.enable_ollama_vm ? 1 : 0
  name    = "${var.ollama_vm_name}-allow-ollama"
  network = local.network_self_link

  allow {
    protocol = "tcp"
    ports    = ["11434"]
  }

  source_ranges = var.ollama_allowed_cidrs
  target_tags   = ["ollama-gpu"]
}

resource "google_service_account" "llm" {
  count        = var.create_service_account ? 1 : 0
  account_id   = var.service_account_name
  display_name = "LLM runtime service account"
}

resource "google_compute_instance" "ollama" {
  count        = var.enable_ollama_vm ? 1 : 0
  name         = var.ollama_vm_name
  zone         = var.zone
  machine_type = var.ollama_machine_type
  tags         = ["ollama-gpu"]

  boot_disk {
    initialize_params {
      image = "projects/${var.ollama_image_project}/global/images/family/${var.ollama_image_family}"
      size  = var.ollama_boot_disk_gb
      type  = "pd-ssd"
    }
  }

  network_interface {
    network    = local.network_self_link
    subnetwork = local.subnetwork_self_link

    access_config {}
  }

  service_account {
    email  = local.service_account_email
    scopes = ["https://www.googleapis.com/auth/cloud-platform"]
  }

  guest_accelerator {
    type  = var.ollama_gpu_type
    count = var.ollama_gpu_count
  }

  scheduling {
    on_host_maintenance = "TERMINATE"
    automatic_restart   = true
  }

  metadata_startup_script = var.ollama_startup_script
}

resource "google_vpc_access_connector" "llm" {
  count         = local.enable_vpc_connector ? 1 : 0
  name          = "llm-connector"
  region        = var.region
  ip_cidr_range = var.vpc_connector_cidr
  network       = local.network_name
}

resource "google_cloud_run_v2_service" "llamacpp" {
  count    = var.enable_llamacpp_service ? 1 : 0
  name     = var.llamacpp_service_name
  location = var.region
  ingress  = var.cloud_run_ingress

  template {
    service_account = local.service_account_email

    containers {
      image = var.llamacpp_image

      ports {
        container_port = var.llamacpp_container_port
      }

      dynamic "env" {
        for_each = var.llamacpp_env
        content {
          name  = env.key
          value = env.value
        }
      }
    }

    vpc_access {
      connector = google_vpc_access_connector.llm[0].name
      egress    = "ALL_TRAFFIC"
    }

    scaling {
      min_instance_count = var.llamacpp_min_instances
      max_instance_count = var.llamacpp_max_instances
    }
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }
}

resource "google_cloud_run_v2_service" "gateway" {
  count    = var.enable_gateway_service ? 1 : 0
  name     = var.gateway_service_name
  location = var.region
  ingress  = var.cloud_run_ingress

  template {
    service_account = local.service_account_email

    containers {
      image = var.gateway_image

      ports {
        container_port = var.gateway_container_port
      }

      dynamic "env" {
        for_each = merge(
          {
            OLLAMA_BASE_URL = var.enable_ollama_vm ? "http://${google_compute_instance.ollama[0].network_interface[0].network_ip}:11434" : ""
            llama_BASE_URL  = var.enable_llamacpp_service ? google_cloud_run_v2_service.llamacpp[0].uri : ""
          },
          var.gateway_env
        )
        content {
          name  = env.key
          value = env.value
        }
      }
    }

    vpc_access {
      connector = google_vpc_access_connector.llm[0].name
      egress    = "ALL_TRAFFIC"
    }

    scaling {
      min_instance_count = var.gateway_min_instances
      max_instance_count = var.gateway_max_instances
    }
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }
}
