output "app_url" {
  description = "URL of the deployed application"
  value       = "http://localhost:8097"
}

output "app_container_name" {
  description = "Name of the application container"
  value       = docker_container.app.name
}

output "node_exporter_target" {
  description = "Prometheus scrape target for Node Exporter"
  value       = "lab8-node-exporter:9100"
}

output "network_name" {
  description = "Docker network for inter-container communication"
  value       = docker_network.lab8.name
}

output "ansible_inventory" {
  description = "Auto-generated Ansible inventory"
  value       = "[local]\nlocalhost ansible_connection=local\n"
}
