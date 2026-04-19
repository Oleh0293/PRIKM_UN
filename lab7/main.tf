terraform {
  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0"
    }
  }
}

provider "docker" {}

resource "docker_image" "nginx" {
  name         = "nginx:latest"
  keep_locally = true
}

resource "docker_container" "web_server" {
  name  = "jenkins-managed-node"
  image = docker_image.nginx.image_id

  ports {
    internal = 80
    external = 8095
  }
}

output "server_ip" {
  value = "localhost"
}

output "server_port" {
  value = "8095"
}
