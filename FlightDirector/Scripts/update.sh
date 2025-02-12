#!/usr/bin/env bash

set -euo pipefail

# Configuration
STATION_ID=${1:-""}
ANSIBLE_PATH="ansible"
PLAYBOOK_FILE="${ANSIBLE_PATH}/playbooks/update.yml"

update_station() {
    log "Updating station ${STATION_ID}..."
    
    ansible-playbook ${PLAYBOOK_FILE} \
        -i ${ANSIBLE_PATH}/inventory/ground_control.yml \
        --limit ${STATION_ID} \
        --tags update \
        --ask-vault-pass
        
    log "Update complete"
}

show_usage() {
    cat << EOF
Usage: $0 STATION_ID

Updates a Ground Control station to the latest version.
EOF
}

main() {
    if [ -z "${STATION_ID}" ]; then
        error "Station ID is required"
    fi
    
    update_station
}

main "$@"
