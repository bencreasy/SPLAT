# ansible/vars/main.yml
# Main variable definitions
splat_version: "0.1.0"
deployment_timestamp: "{{ ansible_date_time.iso8601 }}"

# System Configuration
system_requirements:
  min_memory_mb: 2048
  min_disk_gb: 32
  architecture:
    - aarch64
    - armv7l

system_packages:
  - python3-pip
  - python3-venv
  - git
  - docker.io
  - nginx
  - curl
  - jq
  - htop
  - iotop
  - net-tools

# Docker Configuration
docker_settings:
  compose_version: "2.17.2"
  registry: "gcr.io"
  image_prefix: "splat-project"
  default_tag: "latest"
  network_name: "splat-network"
  restart_policy: "unless-stopped"

# Ground Control Configuration
ground_control:
  image: "{{ docker_settings.registry }}/{{ docker_settings.image_prefix }}/ground-control:{{ docker_settings.default_tag }}"
  container_name: "splat-ground-control"
  port: 8000
  data_path: "/opt/splat/data"
  config_path: "/opt/splat/config"
  logs_path: "/opt/splat/logs"
  environment:
    LOG_LEVEL: "{{ log_level | default('INFO') }}"
    GCP_PROJECT_ID: "{{ gcp_project_id }}"
    GCP_REGION: "{{ gcp_region }}"

# LoRa Configuration
lora:
  device: "/dev/spidev0.0"
  reset_pin: 25
  frequency: 915.0
  bandwidth: 125000
  spreading_factor: 7
  tx_power: 20
  sync_word: 0x42

# Monitoring Configuration
monitoring:
  prometheus:
    image: "prom/prometheus:v2.42.0"
    port: 9090
    retention_days: 15
    scrape_interval: "15s"
    evaluation_interval: "15s"
  
  grafana:
    image: "grafana/grafana:9.4.7"
    port: 3000
    admin_user: "admin"
    plugins:
      - grafana-clock-panel
      - grafana-simple-json-datasource
  
  node_exporter:
    image: "prom/node-exporter:v1.5.0"
    port: 9100

# Deployment Configuration
deployment:
  timeout: 600
  health_check:
    retries: 6
    delay: 10
  backup:
    enabled: true
    retention_days: 30
    path: "/opt/splat/backups"

# Network Configuration
network:
  timeout: 30
  connection_retries: 3
  allowed_ports:
    - "{{ ground_control.port }}"
    - "{{ monitoring.grafana.port }}"
    - 22  # SSH

# ansible/vars/development.yml
---
environment: "development"
log_level: "DEBUG"

ground_control:
  environment:
    DEVELOPMENT_MODE: "true"
    DEBUG: "true"

monitoring:
  prometheus:
    retention_days: 7
  grafana:
    allow_anonymous: true

deployment:
  backup:
    enabled: false

# ansible/vars/staging.yml
---
environment: "staging"
log_level: "INFO"

ground_control:
  environment:
    DEVELOPMENT_MODE: "false"
    DEBUG: "false"

monitoring:
  prometheus:
    retention_days: 15
  grafana:
    allow_anonymous: false

deployment:
  backup:
    enabled: true
    retention_days: 30

# ansible/vars/production.yml
---
environment: "production"
log_level: "WARNING"

ground_control:
  environment:
    DEVELOPMENT_MODE: "false"
    DEBUG: "false"
    STRICT_MODE: "true"

monitoring:
  prometheus:
    retention_days: 30
    evaluation_interval: "30s"
  grafana:
    allow_anonymous: false
    enforce_password_policy: true

deployment:
  backup:
    enabled: true
    retention_days: 90
    schedule: "0 2 * * *"

# ansible/vars/vault.yml (encrypted with ansible-vault)
---
# Sensitive data - should be encrypted with ansible-vault
vault_secrets:
  grafana_admin_password: "{{ vault_grafana_admin_password }}"
  gcp_service_account_key: "{{ vault_gcp_service_account_key }}"
  lora_encryption_key: "{{ vault_lora_encryption_key }}"
  deployment_key: "{{ vault_deployment_key }}"

# Cloud credentials
gcp_credentials:
  project_id: "{{ vault_gcp_project_id }}"
  service_account_key: "{{ vault_gcp_service_account_key }}"

# Database credentials
database_credentials:
  user: "{{ vault_db_user }}"
  password: "{{ vault_db_password }}"
  host: "{{ vault_db_host }}"

# API keys and tokens
api_credentials:
  telemetry_key: "{{ vault_telemetry_key }}"
  monitoring_token: "{{ vault_monitoring_token }}"

# ansible/vars/roles/ground_control.yml
---
# Ground Control specific variables
ground_control_role:
  services:
    - name: "ground-control"
      image: "{{ ground_control.image }}"
      container_name: "{{ ground_control.container_name }}"
      ports:
        - "{{ ground_control.port }}:8000"
      volumes:
        - "{{ ground_control.data_path }}:/data"
        - "{{ ground_control.config_path }}:/config"
        - "{{ ground_control.logs_path }}:/logs"
      environment: "{{ ground_control.environment }}"
      restart: "{{ docker_settings.restart_policy }}"

  config_templates:
    - src: "ground_control.yml.j2"
      dest: "{{ ground_control.config_path }}/config.yml"
    - src: "lora.yml.j2"
      dest: "{{ ground_control.config_path }}/lora.yml"

# ansible/vars/roles/monitoring.yml
---
# Monitoring specific variables
monitoring_role:
  prometheus:
    config_template: "prometheus.yml.j2"
    rules_template: "prometheus_rules.yml.j2"
    storage_path: "{{ ground_control.data_path }}/prometheus"
    
  grafana:
    config_template: "grafana.ini.j2"
    provisioning_path: "{{ ground_control.config_path }}/grafana/provisioning"
    dashboards_path: "{{ ground_control.config_path }}/grafana/dashboards"
    datasources:
      - name: "Prometheus"
        type: "prometheus"
        url: "http://prometheus:9090"
        access: "proxy"
        is_default: true

  dashboards:
    - name: "Ground Control Overview"
      file: "ground_control.json"
    - name: "LoRa Metrics"
      file: "lora_metrics.json"
    - name: "System Metrics"
      file: "system_metrics.json"

# ansible/vars/roles/backup.yml
---
# Backup specific variables
backup_role:
  paths_to_backup:
    - "{{ ground_control.config_path }}"
    - "{{ ground_control.data_path }}/db"
    - "{{ ground_control.logs_path }}"
  
  exclude_patterns:
    - "*.tmp"
    - "*.log"
    - "temp/*"
  
  backup_script_template: "backup.sh.j2"
  cleanup_script_template: "cleanup.sh.j2"
  
  compression: "gzip"
  compression_level: 6
  
  retention:
    daily: 7
    weekly: 4
    monthly: 3
