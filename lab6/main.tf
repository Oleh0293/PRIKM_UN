terraform {
  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0"
    }
  }
}

provider "docker" {}

# ---------- Nginx image ----------
resource "docker_image" "nginx" {
  name         = "nginx:latest"
  keep_locally = true
}

# ---------- Server 1 ----------
resource "docker_container" "web_server_1" {
  name  = "web-app-1"
  image = docker_image.nginx.image_id

  ports {
    internal = 80
    external = 8090
  }
}

# ---------- Server 2 ----------
resource "docker_container" "web_server_2" {
  name  = "web-app-2"
  image = docker_image.nginx.image_id

  ports {
    internal = 80
    external = 8092
  }
}

# ---------- Outputs ----------
output "server_1_name" {
  value = docker_container.web_server_1.name
}

output "server_1_port" {
  value = "8090"
}

output "server_2_name" {
  value = docker_container.web_server_2.name
}

output "server_2_port" {
  value = "8092"
}

output "ansible_inventory" {
  value = "[servers]\nlocalhost ansible_connection=local"
}
