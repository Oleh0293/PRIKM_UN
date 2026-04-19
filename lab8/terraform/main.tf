terraform {
  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0"
    }
  }
}

provider "docker" {}

# ──────────────── Network ────────────────
resource "docker_network" "lab8" {
  name = "lab8-network"
}

# ──────────────── App Node ────────────────
resource "docker_image" "app" {
  name         = "dante0293/prikm:latest"
  keep_locally = true
}

resource "docker_container" "app" {
  name  = "lab8-app"
  image = docker_image.app.image_id

  networks_advanced {
    name = docker_network.lab8.name
  }

  ports {
    internal = 80
    external = 8097
  }
}

# ──────────────── Node Exporter (App Node agent) ────────────────
resource "docker_image" "node_exporter" {
  name         = "prom/node-exporter:latest"
  keep_locally = true
}

resource "docker_container" "node_exporter" {
  name  = "lab8-node-exporter"
  image = docker_image.node_exporter.image_id

  networks_advanced {
    name = docker_network.lab8.name
  }

  ports {
    internal = 9100
    external = 9101
  }
}
