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
