terraform {
  required_version = ">= 1.5"
  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0"
    }
  }
}

provider "docker" {}

# ── змінні ─────────────────────────────────────────────────────────────
variable "app_image" {
  description = "Docker image of TaskTracker app (registry/name:tag)"
  type        = string
  default     = "tasktracker:local"
}

variable "active_color" {
  description = "Який слот зараз обслуговує клієнтів: blue або green"
  type        = string
  default     = "blue"
  validation {
    condition     = contains(["blue", "green"], var.active_color)
    error_message = "active_color must be blue or green"
  }
}

variable "blue_port" {
  type    = number
  default = 8100
}

variable "green_port" {
  type    = number
  default = 8101
}

# ── ізольована мережа ──────────────────────────────────────────────────
resource "docker_network" "cw" {
  name = "cw-network"
}

# ── PostgreSQL (стейтфул) ──────────────────────────────────────────────
resource "docker_image" "postgres" {
  name         = "postgres:16-alpine"
  keep_locally = true
}

resource "docker_volume" "pg_data" {
  name = "cw-pg-data"
}

resource "docker_container" "postgres" {
  name  = "cw-postgres"
  image = docker_image.postgres.image_id
  hostname = "postgres"

  env = [
    "POSTGRES_DB=tasktracker",
    "POSTGRES_USER=tt",
    "POSTGRES_PASSWORD=tt_pass",
  ]

  networks_advanced {
    name    = docker_network.cw.name
    aliases = ["postgres"]
  }

  volumes {
    volume_name    = docker_volume.pg_data.name
    container_path = "/var/lib/postgresql/data"
  }

  healthcheck {
    test         = ["CMD-SHELL", "pg_isready -U tt -d tasktracker"]
    interval     = "10s"
    timeout      = "3s"
    retries      = 5
    start_period = "5s"
  }

  restart = "unless-stopped"
}

# ── Blue slot ──────────────────────────────────────────────────────────
resource "docker_container" "app_blue" {
  name     = "cw-app-blue"
  image    = var.app_image
  hostname = "app-blue"

  env = [
    "VERSION=1.0.0",
    "COLOR=blue",
    "DB_HOST=postgres",
    "DB_PORT=5432",
    "DB_NAME=tasktracker",
    "DB_USER=tt",
    "DB_PASS=tt_pass",
  ]

  networks_advanced {
    name    = docker_network.cw.name
    aliases = ["app-blue"]
  }

  ports {
    internal = 5000
    external = var.blue_port
  }

  depends_on = [docker_container.postgres]
  restart    = "unless-stopped"
}

# ── Green slot ─────────────────────────────────────────────────────────
resource "docker_container" "app_green" {
  name     = "cw-app-green"
  image    = var.app_image
  hostname = "app-green"

  env = [
    "VERSION=1.0.0",
    "COLOR=green",
    "DB_HOST=postgres",
    "DB_PORT=5432",
    "DB_NAME=tasktracker",
    "DB_USER=tt",
    "DB_PASS=tt_pass",
  ]

  networks_advanced {
    name    = docker_network.cw.name
    aliases = ["app-green"]
  }

  ports {
    internal = 5000
    external = var.green_port
  }

  depends_on = [docker_container.postgres]
  restart    = "unless-stopped"
}

# ── Node Exporter — метрики хоста ─────────────────────────────────────
resource "docker_image" "node_exporter" {
  name         = "prom/node-exporter:latest"
  keep_locally = true
}

resource "docker_container" "node_exporter" {
  name     = "cw-node-exporter"
  image    = docker_image.node_exporter.image_id
  hostname = "node-exporter"

  networks_advanced {
    name    = docker_network.cw.name
    aliases = ["node-exporter"]
  }

  ports {
    internal = 9100
    external = 9110
  }

  restart = "unless-stopped"
}
