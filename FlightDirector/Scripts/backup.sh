#!/usr/bin/env bash

set -euo pipefail

# Configuration
BACKUP_DIR="/opt/splat/backups"
DATA_DIR="/opt/splat/data"
CONFIG_DIR="/opt/splat/config"
RETENTION_DAYS=30

create_backup() {
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_file="${BACKUP_DIR}/splat_backup_${timestamp}.tar.gz"
    
    log "Creating backup..."
    
    # Create backup directory if it doesn't exist
    mkdir -p "${BACKUP_DIR}"
    
    # Create tar archive
    tar -czf "${backup_file}" \
        -C "${DATA_DIR}" . \
        -C "${CONFIG_DIR}" .
        
    log "Backup created: ${backup_file}"
}

cleanup_old_backups() {
    log "Cleaning up old backups..."
    
    find "${BACKUP_DIR}" -name "splat_backup_*.tar.gz" -mtime +${RETENTION_DAYS} -delete
    
    log "Cleanup complete"
}

main() {
    create_backup
    cleanup_old_backups
}

main "$@"
