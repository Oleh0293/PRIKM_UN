# Lab 4: Automated Monitoring Deployment with Docker Compose

## Overview

This lab deploys a complete monitoring stack using Docker Compose, including:

- **Prometheus** — metrics collection and storage
- **Node Exporter** — host-level hardware and OS metrics
- **cAdvisor** — container resource usage and performance metrics
- **Grafana** — visualization and dashboarding
- **Jenkins** — CI/CD server with Prometheus metrics plugin

## Architecture

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ Node Exporter│     │   cAdvisor   │     │   Jenkins    │
│   :9100      │     │   :8080      │     │   :8080      │
└──────┬───────┘     └──────┬───────┘     └──────┬───────┘
       │                    │                    │
       └────────────┬───────┘────────────────────┘
                    │
             ┌──────▼───────┐
             │  Prometheus  │
             │   :9090      │
             └──────┬───────┘
                    │
             ┌──────▼───────┐
             │   Grafana    │
             │   :3000      │
             └──────────────┘
```

## Services and Ports

| Service        | Container Name           | Internal Port | External Port |
|----------------|--------------------------|---------------|---------------|
| Prometheus     | monitoring_prometheus    | 9090          | 9090          |
| Node Exporter  | monitoring_node_exporter | 9100          | 9100          |
| cAdvisor       | monitoring_cadvisor      | 8080          | 8082          |
| Grafana        | monitoring_grafana       | 3000          | 3000          |
| Jenkins        | monitoring_jenkins       | 8080          | 8081          |

## Prerequisites

- Docker Engine installed
- Docker Compose v2 installed
- At least 2GB RAM available

## Quick Start

1. Navigate to the lab4 directory on the VM:
   ```bash
   cd /vagrant/lab4
   ```

2. Build and start all services:
   ```bash
   sudo docker compose up -d
   ```

3. Verify all containers are running:
   ```bash
   docker ps
   ```

4. Access the services (replace `<VM_IP>` with your VM's IP):
   - Prometheus: `http://<VM_IP>:9090`
   - Grafana: `http://<VM_IP>:3000` (admin / admin123)
   - Jenkins: `http://<VM_IP>:8081`
   - cAdvisor: `http://<VM_IP>:8082`

## File Structure

```
lab4/
├── docker-compose.yml                          # Main compose definition
├── jenkins/
│   └── Dockerfile                              # Jenkins image with Prometheus plugin
├── prometheus/
│   └── prometheus.yml                          # Prometheus scrape configuration
├── grafana/
│   ├── provisioning/
│   │   ├── datasources/
│   │   │   └── datasources.yml                 # Auto-configure Prometheus datasource
│   │   └── dashboards/
│   │       └── dashboards.yml                  # Dashboard provisioning config
│   └── dashboards/
│       └── jenkins-builds.json                 # Jenkins Builds Dashboard
└── README.md
```

## Prometheus Scrape Targets

| Job Name      | Target             | Description                    |
|---------------|--------------------|--------------------------------|
| prometheus    | localhost:9090     | Prometheus self-monitoring     |
| cadvisor      | cadvisor:8080      | Container metrics              |
| node-exporter | node-exporter:9100 | Host hardware/OS metrics       |
| jenkins       | jenkins:8080       | Jenkins build metrics          |

## Grafana Dashboard

The pre-provisioned **Jenkins Builds Dashboard** includes:

1. **Successful Builds (Total)** — stat panel showing total successful build count
2. **Failed Builds (Total)** — stat panel showing total failed build count
3. **Average Build Duration** — stat panel showing mean build duration in seconds
4. **Jenkins Builds Over Time** — time series chart tracking success/failure trends
5. **Container CPU Usage** — CPU usage of all monitoring stack containers
6. **Container Memory Usage** — memory usage of all monitoring stack containers

## Jenkins Configuration

The Docker Jenkins container comes pre-installed with:

- **Prometheus Metrics** plugin — exposes build metrics at `/prometheus/`
- **Pipeline** plugins — workflow-aggregator, git, pipeline-stage-view

A sample pipeline job (`simple-pipeline`) is configured with Hello, Info, and Test stages.

## Stopping the Stack

```bash
cd /vagrant/lab4
sudo docker compose down
```

To remove all data volumes as well:

```bash
sudo docker compose down -v
```
