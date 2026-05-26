output "network_name" {
  value = docker_network.cw.name
}

output "blue_url" {
  value = "http://localhost:${var.blue_port}"
}

output "green_url" {
  value = "http://localhost:${var.green_port}"
}

output "active_color" {
  value = var.active_color
}

output "active_url" {
  value = var.active_color == "blue" ? "http://localhost:${var.blue_port}" : "http://localhost:${var.green_port}"
}

output "node_exporter_target" {
  value = "node-exporter:9100"
}

output "ansible_inventory" {
  value = "[local]\nlocalhost ansible_connection=local\n"
}
