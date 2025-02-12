# SPLAT FlightDirector - Ansible Configuration

## Directory Structure
```
flight-director/
├── ansible.cfg
├── inventory/
│   ├── ground_control.yml
│   └── group_vars/
│       └── ground_control.yml
├── roles/
│   ├── common/
│   ├── docker/
│   ├── gse/
│   ├── lora/
│   ├── monitoring/
│   └── security/
├── playbooks/
│   ├── site.yml
│   ├── update.yml
│   └── maintenance.yml
└── templates/
    ├── docker-compose.yml.j2
    ├── gse-config.yml.j2
    └── nginx.conf.j2
```

## Core Configuration Files

### ansible.cfg
```ini
[defaults]
inventory = inventory/ground_control.yml
remote_user = pi
host_key_checking = False
roles_path = roles
log_path = logs/ansible.log

[privilege_escalation]
become = True
become_method = sudo
```

### inventory/ground_control.yml
```yaml
all:
  children:
    ground_control:
      hosts:
        gse_pi:
          ansible_host: 192.168.1.100
          ansible_user: pi
```

### inventory/group_vars/ground_control.yml
```yaml
---
# Ground Control Configuration
gse_version: "1.0.0"
gse_environment: "development"

# System Configuration
timezone: "UTC"
locale: "en_US.UTF-8"
hostname: "splat-ground-control"

# Docker Configuration
docker_compose_version: "2.17.2"
docker_users:
  - pi

# Network Configuration
wifi_country: "US"
wifi_ssid: "{{ vault_wifi_ssid }}"
wifi_password: "{{ vault_wifi_password }}"

# GCP Configuration
gcp_project_id: "{{ vault_gcp_project_id }}"
gcp_region: "us-central1"

# LoRa Configuration
lora_frequency: 915.0
lora_bandwidth: 125000
lora_spreading_factor: 7
lora_tx_power: 20

# Monitoring Configuration
enable_monitoring: true
prometheus_retention_days: 15
grafana_admin_password: "{{ vault_grafana_password }}"
```

## Playbooks

### playbooks/site.yml
```yaml
---
- name: Configure Ground Control Station
  hosts: ground_control
  become: yes
  
  pre_tasks:
    - name: Update apt cache
      apt:
        update_cache: yes
        cache_valid_time: 3600

  roles:
    - common
    - docker
    - lora
    - gse
    - monitoring
    - security

  post_tasks:
    - name: Verify GSE services
      uri:
        url: "http://localhost:3000/health"
        return_content: yes
      register: health_check
      until: health_check.status == 200
      retries: 6
      delay: 10
```

## Roles

### roles/common/tasks/main.yml
```yaml
---
- name: Set timezone
  timezone:
    name: "{{ timezone }}"

- name: Install required packages
  apt:
    name:
      - git
      - python3-pip
      - python3-venv
      - build-essential
      - nginx
      - ufw
    state: present

- name: Configure hostname
  hostname:
    name: "{{ hostname }}"

- name: Update hosts file
  template:
    src: hosts.j2
    dest: /etc/hosts
    mode: '0644'
```

### roles/docker/tasks/main.yml
```yaml
---
- name: Install Docker dependencies
  apt:
    name:
      - apt-transport-https
      - ca-certificates
      - curl
      - gnupg
      - lsb-release
    state: present

- name: Add Docker GPG key
  apt_key:
    url: https://download.docker.com/linux/debian/gpg
    state: present

- name: Add Docker repository
  apt_repository:
    repo: deb [arch=arm64] https://download.docker.com/linux/debian bullseye stable
    state: present

- name: Install Docker
  apt:
    name:
      - docker-ce
      - docker-ce-cli
      - containerd.io
    state: present

- name: Install Docker Compose
  get_url:
    url: "https://github.com/docker/compose/releases/download/v{{ docker_compose_version }}/docker-compose-linux-aarch64"
    dest: /usr/local/bin/docker-compose
    mode: '0755'
```

### roles/gse/tasks/main.yml
```yaml
---
- name: Create GSE directories
  file:
    path: "{{ item }}"
    state: directory
    mode: '0755'
  with_items:
    - /opt/splat/gse
    - /opt/splat/data
    - /opt/splat/config
    - /opt/splat/logs

- name: Copy GSE configuration
  template:
    src: gse-config.yml.j2
    dest: /opt/splat/config/gse-config.yml
    mode: '0644'

- name: Deploy Docker Compose configuration
  template:
    src: docker-compose.yml.j2
    dest: /opt/splat/docker-compose.yml
    mode: '0644'

- name: Pull Docker images
  docker_compose:
    project_src: /opt/splat
    pull: yes

- name: Start GSE services
  docker_compose:
    project_src: /opt/splat
    state: present
```

### roles/lora/tasks/main.yml
```yaml
---
- name: Install LoRa dependencies
  apt:
    name:
      - python3-pip
      - python3-rpi.gpio
      - wiringpi
    state: present

- name: Configure SPI interface
  lineinfile:
    path: /boot/config.txt
    line: "dtoverlay=spi0-hw-cs"
    state: present

- name: Install Python LoRa library
  pip:
    name: adafruit-circuitpython-rfm9x
    state: present

- name: Copy LoRa configuration
  template:
    src: lora-config.yml.j2
    dest: /opt/splat/config/lora-config.yml
    mode: '0644'
```

## Templates

### templates/docker-compose.yml.j2
```yaml
version: '3.8'

services:
  influxdb:
    image: influxdb:2.0
    volumes:
      - /opt/splat/data/influxdb:/var/lib/influxdb2
    ports:
      - "8086:8086"
    environment:
      - DOCKER_INFLUXDB_INIT_MODE=setup
      - DOCKER_INFLUXDB_INIT_USERNAME=admin
      - DOCKER_INFLUXDB_INIT_PASSWORD={{ vault_influxdb_password }}
      - DOCKER_INFLUXDB_INIT_ORG=splat
      - DOCKER_INFLUXDB_INIT_BUCKET=telemetry

  grafana:
    image: grafana/grafana
    volumes:
      - /opt/splat/data/grafana:/var/lib/grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD={{ grafana_admin_password }}

  gse:
    build: 
      context: /opt/splat/gse
    volumes:
      - /opt/splat/config:/config
      - /opt/splat/data:/data
    ports:
      - "8000:8000"
    environment:
      - GSE_ENV={{ gse_environment }}
      - GCP_PROJECT_ID={{ gcp_project_id }}
    devices:
      - "/dev/spidev0.0:/dev/spidev0.0"
```

### templates/gse-config.yml.j2
```yaml
# GSE Configuration
version: {{ gse_version }}
environment: {{ gse_environment }}

# LoRa Configuration
lora:
  frequency: {{ lora_frequency }}
  bandwidth: {{ lora_bandwidth }}
  spreading_factor: {{ lora_spreading_factor }}
  tx_power: {{ lora_tx_power }}

# Cloud Configuration
gcp:
  project_id: {{ gcp_project_id }}
  region: {{ gcp_region }}

# Data Storage
storage:
  path: /data
  retention_days: 30

# Monitoring
monitoring:
  enabled: {{ enable_monitoring }}
  metrics_port: 9090
```

## Usage Instructions

```bash
# Check syntax
ansible-playbook playbooks/site.yml --syntax-check

# Run playbook with vault
ansible-playbook playbooks/site.yml --ask-vault-pass

# Update GSE components
ansible-playbook playbooks/update.yml --tags gse

# Run maintenance tasks
ansible-playbook playbooks/maintenance.yml
```

## Notes:
1. Security Considerations:
   - Vault for sensitive data
   - UFW firewall configuration
   - Secure defaults
   - Regular updates

2. Development Features:
   - Easy configuration
   - Development environment
   - Monitoring included
   - Quick updates

3. Maintenance:
   - Backup configuration
   - Update procedures
   - Health checks
   - Logging setup
