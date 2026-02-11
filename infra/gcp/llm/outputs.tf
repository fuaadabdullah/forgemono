output "ollama_vm_public_ip" {
  description = "Public IP for the Ollama GPU VM"
  value       = var.enable_ollama_vm ? google_compute_instance.ollama[0].network_interface[0].access_config[0].nat_ip : null
}

output "ollama_vm_private_ip" {
  description = "Private IP for the Ollama GPU VM"
  value       = var.enable_ollama_vm ? google_compute_instance.ollama[0].network_interface[0].network_ip : null
}

output "llamacpp_url" {
  description = "Cloud Run URL for llama.cpp"
  value       = var.enable_llamacpp_service ? google_cloud_run_v2_service.llamacpp[0].uri : null
}

output "gateway_url" {
  description = "Cloud Run URL for the model gateway"
  value       = var.enable_gateway_service ? google_cloud_run_v2_service.gateway[0].uri : null
}

output "vpc_connector" {
  description = "Cloud Run VPC connector name"
  value       = local.enable_vpc_connector ? google_vpc_access_connector.llm[0].name : null
}
