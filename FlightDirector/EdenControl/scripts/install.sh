#!/bin/bash
# install.sh

# Ensure running as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root"
  exit 1
fi

# Set variables
INSTALL_DIR="/opt/eden"
USER="pi"
GROUP="pi"

# Create installation directory
mkdir -p $INSTALL_DIR
mkdir -p $INSTALL_DIR/config
mkdir -p $INSTALL_DIR/logs

# Install system dependencies
apt update
apt install -y python3-pip python3-dev python3-pygame python3-yaml libsdl2-dev

# Create virtual environment
python3 -m pip install virtualenv
python3 -m virtualenv $INSTALL_DIR/venv

# Install Python dependencies
$INSTALL_DIR/venv/bin/pip install pyyaml requests pygame

# Copy files to installation directory
cp -r eden_control $INSTALL_DIR/
cp config/default.yml $INSTALL_DIR/config/

# Create systemd service file
cat > /etc/systemd/system/eden.service << EOL
[Unit]
Description=Eden Control System
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$INSTALL_DIR
ExecStart=$INSTALL_DIR/venv/bin/python -m eden_control.main --config $INSTALL_DIR/config/default.yml
Restart=on-failure
RestartSec=5
StandardOutput=syslog
StandardError=syslog
SyslogIdentifier=eden

[Install]
WantedBy=multi-user.target
EOL

# Set permissions
chown -R $USER:$GROUP $INSTALL_DIR
chmod +x $INSTALL_DIR/eden_control/main.py

# Enable and start service
systemctl daemon-reload
systemctl enable eden.service
systemctl start eden.service

echo "Eden Control System installed at $INSTALL_DIR"
echo "Service status:"
systemctl status eden.service
