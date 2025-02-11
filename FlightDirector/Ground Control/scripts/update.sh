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
