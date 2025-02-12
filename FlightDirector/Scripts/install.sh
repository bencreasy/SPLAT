#!/usr/bin/env bash

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Configuration
PYTHON_VERSION="3.9"
VENV_PATH="venv"
REQUIREMENTS_FILE="requirements.txt"
CONFIG_TEMPLATE="config/default.yml"

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}" >&2
    exit 1
}

warn() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

check_prerequisites() {
    log "Checking prerequisites..."
    
    # Check Python version
    if ! command -v python${PYTHON_VERSION} &> /dev/null; then
        error "Python ${PYTHON_VERSION} is required but not installed"
    fi
    
    # Check pip
    if ! command -v pip3 &> /dev/null; then
        error "pip3 is required but not installed"
    fi
    
    # Check ansible
    if ! command -v ansible &> /dev/null; then
        error "Ansible is required but not installed"
    }
    
    log "Prerequisites check passed"
}

setup_virtual_environment() {
    log "Setting up virtual environment..."
    
    python${PYTHON_VERSION} -m venv ${VENV_PATH}
    source ${VENV_PATH}/bin/activate
    
    pip install --upgrade pip
    pip install -r ${REQUIREMENTS_FILE}
    
    log "Virtual environment setup complete"
}

initialize_configuration() {
    log "Initializing configuration..."
    
    if [ ! -f ${CONFIG_TEMPLATE} ]; then
        error "Configuration template not found: ${CONFIG_TEMPLATE}"
    fi
    
    # Create configuration directory
    mkdir -p config
    
    # Copy configuration template
    cp ${CONFIG_TEMPLATE} config/config.yml
    
    log "Configuration initialized"
}

main() {
    log "Starting Flight Director installation..."
    
    check_prerequisites
    setup_virtual_environment
    initialize_configuration
    
    log "Installation complete"
}

main "$@"
