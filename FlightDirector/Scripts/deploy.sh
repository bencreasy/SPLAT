#!/usr/bin/env bash

set -euo pipefail

# Configuration
ANSIBLE_PATH="ansible"
INVENTORY_FILE="${ANSIBLE_PATH}/inventory/ground_control.yml"
PLAYBOOK_FILE="${ANSIBLE_PATH}/playbooks/site.yml"

# Parse command line arguments
parse_args() {
    while getopts "e:s:h" opt; do
        case ${opt} in
            e)
                ENVIRONMENT=$OPTARG
                ;;
            s)
                STATION_ID=$OPTARG
                ;;
            h)
                show_usage
                exit 0
                ;;
            \?)
                error "Invalid option: -$OPTARG"
                ;;
        esac
    done
    
    if [ -z "${ENVIRONMENT:-}" ]; then
        error "Environment (-e) is required"
    fi
    
    if [ -z "${STATION_ID:-}" ]; then
        error "Station ID (-s) is required"
    fi
}

deploy_ground_control() {
    log "Deploying Ground Control station ${STATION_ID} in ${ENVIRONMENT} environment..."
    
    # Run ansible playbook
    ansible-playbook ${PLAYBOOK_FILE} \
        -i ${INVENTORY_FILE} \
        --limit ${STATION_ID} \
        -e "environment=${ENVIRONMENT}" \
        --ask-vault-pass
        
    log "Deployment complete"
}

show_usage() {
    cat << EOF
Usage: $0 -e ENVIRONMENT -s STATION_ID

Options:
    -e ENVIRONMENT   Deployment environment (development|staging|production)
    -s STATION_ID    Ground Control station ID
    -h              Show this help message
EOF
}

main() {
    parse_args "$@"
    deploy_ground_control
}

main "$@"
