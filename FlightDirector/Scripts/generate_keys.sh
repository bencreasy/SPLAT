#!/usr/bin/env bash

set -euo pipefail

# Configuration
KEYS_DIR="keys"
DEPLOYMENT_ID=${1:-""}

generate_deployment_keys() {
    local deployment_dir="${KEYS_DIR}/deployments/${DEPLOYMENT_ID}"
    
    log "Generating keys for deployment ${DEPLOYMENT_ID}..."
    
    # Create deployment directory
    mkdir -p "${deployment_dir}"
    
    # Generate RSA key pair
    openssl genpkey -algorithm RSA -out "${deployment_dir}/private.pem" -pkeyopt rsa_keygen_bits:2048
    openssl rsa -pubout -in "${deployment_dir}/private.pem" -out "${deployment_dir}/public.pem"
    
    # Generate encryption key
    openssl rand -base64 32 > "${deployment_dir}/encryption.key"
    
    # Set appropriate permissions
    chmod 600 "${deployment_dir}/private.pem"
    chmod 644 "${deployment_dir}/public.pem"
    chmod 600 "${deployment_dir}/encryption.key"
    
    log "Keys generated successfully"
}

show_usage() {
    cat << EOF
Usage: $0 DEPLOYMENT_ID

Generates necessary keys for a Flight Director deployment.
EOF
}

main() {
    if [ -z "${DEPLOYMENT_ID}" ]; then
        error "Deployment ID is required"
    fi
    
    generate_deployment_keys
}

main "$@"
