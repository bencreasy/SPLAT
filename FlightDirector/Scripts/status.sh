#!/usr/bin/env bash

set -euo pipefail

# Configuration
STATION_ID=${1:-""}

check_station_status() {
    log "Checking status of station ${STATION_ID}..."
    
    # Check if station is responding
    if curl -sf "http://${STATION_ID}:8000/health" > /dev/null; then
        log "Station ${STATION_ID} is healthy"
        
        # Get detailed status
        curl -s "http://${STATION_ID}:8000/status" | jq .
    else
        error "Station ${STATION_ID} is not responding"
    fi
}

show_usage() {
    cat << EOF
Usage: $0 STATION_ID

Checks the status of a Ground Control station.
EOF
}

main() {
    if [ -z "${STATION_ID}" ]; then
        error "Station ID is required"
    fi
    
    check_station_status
}

main "$@"
