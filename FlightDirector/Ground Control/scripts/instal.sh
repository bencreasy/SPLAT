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
