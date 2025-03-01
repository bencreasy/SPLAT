
# SPLAT Ground Systems 🛰️

SPLAT (Soil Permeability Logging Analyitics Transponder) Ground Systems provides the infrastructure and configuration management for SPLAT's backend operations.

## Overview

This repository contains two main components:

### 🚀 LaunchPad
Infrastructure as Code (Terraform) deployment for SPLAT's cloud infrastructure. LaunchPad manages all cloud resources required for SPLAT operations, including IoT Core, message queues, data storage, and processing functions.

### 🎮 FlightDirector
Ansible configuration management for SPLAT Ground Control stations. FlightDirector handles the deployment and management of local ground station software, including LoRa communication, data processing, and monitoring systems.

## System Architecture

## Prerequisites

### Software Requirements
- Terraform >= 1.0.0
- Ansible >= 2.9
- Python >= 3.9
- Google Cloud SDK
- Git

### Hardware Requirements
- Raspberry Pi 4 (4GB+ RAM)
- LoRa concentrator
- Storage (32GB+ recommended)
- Stable network connection

## Quick Start

### LaunchPad Deployment

```bash
# Clone repository
git clone https://github.com/bencreasy/splat/launchpad.git
cd splat-ground-systems/launchpad

# Initialize Terraform
terraform init

# Create development workspace
terraform workspace new dev

# Deploy infrastructure
terraform plan -var-file=environments/dev.tfvars
terraform apply -var-file=environments/dev.tfvars
```

### FlightDirector Setup

```bash
# Navigate to FlightDirector
cd ../flight-director

# Create vault password file
echo "your-secure-password" > .vault_pass

# Update inventory
cp inventory/ground_control.example.yml inventory/ground_control.yml
# Edit with your Ground Control IP

# Deploy Ground Control software
ansible-playbook playbooks/site.yml
```

## Component Details

### LaunchPad Components

- **Mission Control**: IoT Core and Pub/Sub configuration
- **Ground Station**: Cloud Functions and data processing
- **Telemetry**: Storage and database configuration
- **Security**: IAM and authentication setup

```hcl
module "mission_control" {
  source = "./modules/mission_control"
  # ... configuration ...
}
```

### FlightDirector Components

- **System Configuration**: Basic system setup and hardening
- **Docker Environment**: Container runtime and orchestration
- **GSE Software**: Ground station software deployment
- **LoRa Interface**: Radio communication setup
- **Monitoring**: System and application monitoring

```yaml
- name: Deploy Ground Control
  hosts: ground_control
  roles:
    - common
    - docker
    - gse
    - lora
    - monitoring
```

## Development

### Local Development Environment

```bash
# Set up development environment
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Start local services
docker-compose -f docker-compose.dev.yml up
```

### Testing

```bash
# LaunchPad
cd launchpad
terraform fmt -check
terraform validate

# FlightDirector
cd flight-director
ansible-playbook --syntax-check playbooks/site.yml
```

## Deployment

### Environment Configuration

- `dev`: Development environment
- `staging`: Testing environment
- `prod`: Production environment

```bash
# Select environment
terraform workspace select dev|staging|prod

# Deploy with appropriate variables
terraform apply -var-file=environments/$(terraform workspace show).tfvars
```

## Monitoring

### Available Dashboards

- System Health: `http://ground-control:3000/d/system`
- LoRa Metrics: `http://ground-control:3000/d/lora`
- Data Flow: `http://ground-control:3000/d/flow`

### Key Metrics

- Packet Success Rate
- Signal Strength
- System Resource Usage
- Data Processing Latency

## Maintenance

### Regular Tasks

```bash
# Update GSE software
ansible-playbook playbooks/update.yml --tags gse

# System updates
ansible-playbook playbooks/maintenance.yml

# Backup configuration
ansible-playbook playbooks/backup.yml
```



