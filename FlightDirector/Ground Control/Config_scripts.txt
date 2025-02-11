# Ground Control Configuration and Scripts

## Directory Structure
```
ground_control/
├── config/
│   ├── default.yml           # Default configuration
│   ├── modules.yml           # Module-specific configs
│   ├── secrets.yml.enc       # Encrypted secrets
│   └── templates/            # Configuration templates
│       ├── development.yml
│       ├── production.yml
│       └── testing.yml
│
└── scripts/
    ├── install.sh           # Installation script
    ├── update.sh            # Update script
    ├── backup.sh            # Backup script
    ├── utils/               # Utility scripts
    │   ├── encrypt.py       # Secret encryption
    │   ├── validate.py      # Config validation
    │   └── setup_display.py # Display setup
    └── tests/               # Test scripts
        ├── hardware_test.sh
        └── network_test.sh
```

## Configuration Files

### 1. Default Configuration (default.yml)
```yaml
# System-wide configuration
system:
  name: "ground_control"
  version: "0.1.0"
  environment: "development"
  time_zone: "UTC"
  log_level: "INFO"
  data_dir: "/data/ground_control"

# Network configuration
network:
  hostname: "splat-gc-${DEVICE_ID}"
  wifi:
    enabled: false
    ssid: ""
    psk: ""
  ethernet:
    enabled: true
    dhcp: true
    static_ip: ""
    gateway: ""
    dns: []

# Security settings
security:
  encryption_key: "${ENCRYPTION_KEY}"
  allow_remote_access: false
  allowed_ips: []
  ssh:
    enabled: true
    port: 22
    allow_password: false
    allow_key_auth: true

# Update settings
updates:
  auto_update: true
  check_interval: 86400  # 24 hours
  update_hour: 3        # 3 AM
  backup_before_update: true
```

### 2. Module Configuration (modules.yml)
```yaml
# LoRa configuration
lora:
  enabled: true
  device: "/dev/spidev0.0"
  frequency: 915.0
  bandwidth: 125000
  spreading_factor: 7
  coding_rate: 5
  tx_power: 20
  sync_word: 0x12

# Storage configuration
storage:
  enabled: true
  max_buffer_size: "100M"
  max_storage: "10G"
  backup_enabled: true
  backup_interval: 86400
  cleanup_age: 30  # days

# Display configuration
display:
  enabled: true
  type: "ssd1306"
  width: 128
  height: 64
  i2c_address: "0x3C"
  rotation: 0
  contrast: 255
  update_interval: 1

# Cloud configuration
cloud:
  enabled: true
  project_id: "${GCP_PROJECT_ID}"
  region: "${GCP_REGION}"
  retry_attempts: 3
  retry_delay: 30
  batch_size: 100
  sync_interval: 60

# Monitor configuration
monitor:
  enabled: true
  check_interval: 60
  metrics_interval: 300
  alert_retention: 604800  # 7 days
  thresholds:
    cpu_warning: 80
    cpu_critical: 90
    memory_warning: 80
    memory_critical: 90
    disk_warning: 80
    disk_critical: 90
    temp_warning: 70
    temp_critical: 80
```

## Scripts

### 1. Installation Script (install.sh)
```bash
#!/bin/bash
set -e

# Configuration
REPO_URL="https://github.com/your-org/ground-control.git"
INSTALL_DIR="/opt/ground_control"
DATA_DIR="/data/ground_control"
LOG_DIR="/var/log/ground_control"

# Functions
setup_system() {
    echo "Setting up system dependencies..."
    apt-get update
    apt-get install -y \
        python3 python3-pip \
        git docker.io \
        i2c-tools spi-tools

    # Enable required interfaces
    raspi-config nonint do_i2c 0
    raspi-config nonint do_spi 0
}

setup_directories() {
    echo "Creating directories..."
    mkdir -p "$INSTALL_DIR" "$DATA_DIR" "$LOG_DIR"
    chown -R ground_control:ground_control \
        "$INSTALL_DIR" "$DATA_DIR" "$LOG_DIR"
}

install_software() {
    echo "Installing Ground Control..."
    git clone "$REPO_URL" "$INSTALL_DIR"
    cd "$INSTALL_DIR"
    
    # Install Python dependencies
    python3 -m pip install -r requirements.txt
    
    # Install service
    cp systemd/ground-control.service /etc/systemd/system/
    systemctl daemon-reload
    systemctl enable ground-control
}

configure_system() {
    echo "Configuring system..."
    # Generate encryption key
    ENCRYPTION_KEY=$(openssl rand -hex 32)
    
    # Create configuration
    envsubst < config/templates/production.yml > config/default.yml
    
    # Encrypt secrets
    ./scripts/utils/encrypt.py \
        --key "$ENCRYPTION_KEY" \
        --input config/secrets.yml \
        --output config/secrets.yml.enc
}

main() {
    echo "Starting Ground Control installation..."
    
    setup_system
    setup_directories
    install_software
    configure_system
    
    echo "Installation complete!"
}

main "$@"
```

### 2. Update Script (update.sh)
```bash
#!/bin/bash
set -e

# Configuration
BACKUP_DIR="/data/ground_control/backups"
UPDATE_LOG="/var/log/ground_control/update.log"

# Functions
backup_system() {
    echo "Creating backup..."
    ./scripts/backup.sh
}

update_software() {
    echo "Updating software..."
    cd "$INSTALL_DIR"
    
    # Get latest code
    git fetch origin
    git checkout "$(git tag | sort -V | tail -n1)"
    
    # Update dependencies
    python3 -m pip install -r requirements.txt
    
    # Update configuration
    ./scripts/utils/validate.py --config config/default.yml
}

restart_services() {
    echo "Restarting services..."
    systemctl restart ground-control
}

main() {
    echo "Starting update at $(date)" >> "$UPDATE_LOG"
    
    if [ "$AUTO_UPDATE" = "true" ]; then
        backup_system
    fi
    
    update_software
    restart_services
    
    echo "Update completed at $(date)" >> "$UPDATE_LOG"
}

main "$@"
```

### 3. Backup Script (backup.sh)
```bash
#!/bin/bash
set -e

# Configuration
BACKUP_DIR="/data/ground_control/backups"
MAX_BACKUPS=7

# Functions
create_backup() {
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_file="$BACKUP_DIR/backup_$timestamp.tar.gz"
    
    echo "Creating backup: $backup_file"
    
    # Backup configuration
    tar -czf "$backup_file" \
        -C /opt/ground_control/config . \
        -C /data/ground_control data \
        -C /var/log/ground_control logs
        
    # Encrypt backup
    ./scripts/utils/encrypt.py \
        --key "$ENCRYPTION_KEY" \
        --input "$backup_file" \
        --output "$backup_file.enc"
        
    rm "$backup_file"
}

cleanup_old_backups() {
    echo "Cleaning old backups..."
    ls -t "$BACKUP_DIR"/*.enc | \
        tail -n +$((MAX_BACKUPS + 1)) | \
        xargs -r rm
}

main() {
    echo "Starting backup..."
    
    mkdir -p "$BACKUP_DIR"
    create_backup
    cleanup_old_backups
    
    echo "Backup complete!"
}

main "$@"
```

### 4. Configuration Validation (utils/validate.py)
```python
#!/usr/bin/env python3
import yaml
import jsonschema
import sys

def load_schema():
    """Load configuration schema"""
    with open('config/schema.yml', 'r') as f:
        return yaml.safe_load(f)

def validate_config(config_path):
    """Validate configuration file"""
    schema = load_schema()
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    try:
        jsonschema.validate(config, schema)
        print(f"Configuration {config_path} is valid")
        return True
    except jsonschema.exceptions.ValidationError as e:
        print(f"Configuration error: {str(e)}")
        return False

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: validate.py <config_file>")
        sys.exit(1)
        
    if not validate_config(sys.argv[1]):
        sys.exit(1)
```

## Key Features

1. Configuration Management:
   - Environment-specific configs
   - Secure secrets handling
   - Validation system
   - Template-based setup

2. Installation:
   - Automated setup
   - Dependency management
   - Service configuration
   - Security setup

3. Maintenance:
   - Automated updates
   - Backup system
   - Validation tools
   - Monitoring setup

4. Security:
   - Encrypted secrets
   - Secure defaults
   - Access control
   - Backup encryption
