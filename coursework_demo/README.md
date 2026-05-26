# Coursework — TaskTracker Blue/Green DevOps Pipeline

Демонстраційне DevOps-рішення для курсової роботи
«Інтеграція DevOps практик в процеси розробки та розгортання».

## Архітектура

```
                                     ┌────────────────────────┐
                                     │       Developer        │
                                     │  git push → GitHub     │
                                     └────────────┬───────────┘
                                                  │ webhook
                                                  ▼
                                     ┌────────────────────────┐
                                     │       Jenkins          │
                                     │ Pipeline-as-Code (Jfile)│
                                     └────────────┬───────────┘
                                                  │
        ┌─────────────────────┬───────────────────┼───────────────────┐
        ▼                     ▼                   ▼                   ▼
┌──────────────┐    ┌────────────────┐  ┌─────────────────┐  ┌──────────────┐
│ Docker build │    │ Docker Hub     │  │ Terraform Apply │  │ Ansible      │
│  + tests     │    │ (registry)     │  │ (Docker network,│  │ (Monitoring  │
│              │    │                │  │  Postgres, Blue,│  │  + Reverse   │
│              │    │                │  │  Green, NodeExp)│  │  Proxy)      │
└──────────────┘    └────────────────┘  └────────┬────────┘  └──────┬───────┘
                                                 │                  │
                                                 ▼                  ▼
                                  ┌──────────────────────────────────────┐
                                  │  cw-network (Docker bridge)          │
                                  │                                      │
                                  │   ┌──────────┐   ┌─────────────┐    │
                                  │   │  cw-proxy │ → │ cw-app-blue │    │
                                  │   │  (NGINX)  │   └─────────────┘    │
                                  │   │  :8090    │   ┌─────────────┐    │
                                  │   │           │ → │ cw-app-green│    │
                                  │   └─────┬─────┘   └─────────────┘    │
                                  │         │                            │
                                  │         ▼                            │
                                  │   ┌──────────────┐ ┌────────────┐   │
                                  │   │ cw-postgres  │ │ node-exp.  │   │
                                  │   └──────────────┘ └────────────┘   │
                                  │                                      │
                                  │   ┌──────────────┐ ┌────────────┐   │
                                  │   │ cw-prometheus│ │ cw-grafana │   │
                                  │   │   :9099      │ │   :3010    │   │
                                  │   └──────────────┘ └────────────┘   │
                                  └──────────────────────────────────────┘
```

## Структура

```
coursework_demo/
├── app/
│   ├── app.py              # Flask REST API (TaskTracker)
│   ├── requirements.txt
│   └── Dockerfile          # multi-stage build
├── terraform/
│   ├── main.tf             # Postgres + Blue + Green + NodeExporter
│   └── outputs.tf          # outputs (active_url, ansible_inventory)
├── ansible/
│   ├── playbook.yml        # Prometheus + Grafana + NGINX reverse-proxy
│   └── templates/
│       ├── prometheus.yml.j2
│       ├── datasource.yml.j2
│       ├── proxy.conf.j2
│       └── tasktracker-dashboard.json
├── Jenkinsfile             # End-to-end pipeline
└── README.md
```

## Порти

| Сервіс          | Порт |
|-----------------|------|
| Reverse proxy   | 8090 |
| Blue (direct)   | 8100 |
| Green (direct)  | 8101 |
| Prometheus      | 9099 |
| Grafana         | 3010 |
| Node Exporter   | 9110 |

## Запуск

```bash
cd coursework_demo
docker build -t tasktracker:local ./app
cd terraform && terraform init && terraform apply -auto-approve
cd ../ansible && ansible-playbook -i inventory.ini playbook.yml \
    -e active_color=blue
```
