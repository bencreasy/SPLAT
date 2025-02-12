# SPLAT Flight Director 🛩️

Flight Director is the automation and orchestration system for SPLAT (Soil Permeability & Logging Analysis Transponder) deployments. It manages the deployment, configuration, and monitoring of Ground Control stations and LaunchPad infrastructure.

## Quick Start Guide 🚀

### Initial Setup

1. Clone the repository:
```bash
git clone https://github.com/your-org/splat-flight-director.git
cd splat-flight-director
```

2. Create Python virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
pip install -r requirements.txt
```

3. Generate encryption keys:
```bash
# Create secure keys directory
sudo mkdir -p /opt/splat/keys
sudo chmod 700 /opt/splat/keys

# Generate initial encryption key
./scripts/generate_keys.sh initial-setup
```

4. Configure your environment:
```bash
# Copy configuration templates
cp config/default.yml config/development.yml
cp ansible/inventory/ground_control.yml.example ansible/inventory/ground_control.yml

# Edit configurations with your settings
vim config/development.yml
vim ansible/inventory/ground_control.yml
```

### First Deployment

1. Prepare your Ground Control station:
```bash
# Verify SSH access
ssh pi@<ground-control-ip>

# Test connectivity
./scripts/status.sh <station-id>
```

2. Deploy Ground Control:
```bash
# Deploy with development configuration
./scripts/deploy.sh -e development -s <station-id>

# Verify deployment
./scripts/status.sh <station-id>
```

3. Configure LaunchPad:
```bash
# Initialize GCP project
gcloud init

# Deploy LaunchPad infrastructure
./scripts/deploy.sh -e development -s <station-id> --tags launchpad
```

## Project Structure 📁

```
flight-director/
├── src/                      # Source code
│   ├── core/                 # Core Flight Director functionality
│   ├── ansible/              # Ansible automation
│   ├── config/              # Configuration management
│   └── security/            # Security and key management
│
├── ansible/                  # Ansible configurations
│   ├── inventory/           # Station inventory
│   ├── playbooks/           # Deployment playbooks
│   ├── roles/               # Role definitions
│   └── vars/                # Variable definitions
│
├── config/                   # Configuration files
│   ├── default.yml          # Default configuration
│   ├── development.yml      # Development environment
│   └── production.yml       # Production environment
│
├── scripts/                  # Utility scripts
│   ├── install.sh           # Installation script
│   ├── deploy.sh            # Deployment script
│   └── generate_keys.sh     # Key generation
│
└── tests/                   # Test suites
    ├── unit/                # Unit tests
    └── integration/         # Integration tests
```

## Development Setup 🔧

### Local Development Environment

1. Setup development tools:
```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install
```

2. Create test configuration:
```bash
cp config/default.yml config/test.yml
# Edit test.yml with test settings
```

3. Prepare test environment:
```bash
# Create test keys
./scripts/generate_keys.sh test-deployment

# Initialize test database
./scripts/install.sh --env test
```

### Running Tests

1. Unit Tests:
```bash
# Run all unit tests
pytest tests/unit/

# Run specific test file
pytest tests/unit/test_director.py

# Run with coverage
pytest --cov=src tests/
```

2. Integration Tests:
```bash
# Start test environment
./scripts/deploy.sh -e test -s test-station

# Run integration tests
pytest tests/integration/

# Cleanup test environment
./scripts/cleanup.sh test-station
```

## Deployment Guide 📦

### Environment Setup

1. Production Environment:
```bash
# Create production configuration
cp config/default.yml config/production.yml

# Generate production keys
./scripts/generate_keys.sh prod-initial

# Configure Ansible inventory
cp ansible/inventory/ground_control.yml.example ansible/inventory/production.yml
```

2. Security Configuration:
```bash
# Set up Ansible Vault
ansible-vault create ansible/vars/vault.yml

# Add sensitive variables
ansible-vault edit ansible/vars/vault.yml
```

3. Ground Control Preparation:
```bash
# Verify system requirements
./scripts/check_requirements.sh <station-id>

# Configure network
./scripts/configure_network.sh <station-id>
```

### Deployment Process

1. Initial Deployment:
```bash
# Deploy Ground Control
./scripts/deploy.sh -e production -s <station-id>

# Deploy LaunchPad
./scripts/deploy.sh -e production -s <station-id> --tags launchpad

# Verify deployment
./scripts/status.sh <station-id>
```

2. Monitoring Setup:
```bash
# Configure monitoring
./scripts/deploy.sh -e production -s <station-id> --tags monitoring

# Access dashboards
open http://<station-ip>:3000
```

3. Backup Configuration:
```bash
# Enable backups
./scripts/deploy.sh -e production -s <station-id> --tags backup

# Verify backup
./scripts/backup.sh --verify <station-id>
```

## Integration Testing 🧪

### Test Environment Setup

1. Prepare Test Station:
```bash
# Create test station
./scripts/deploy.sh -e test -s test-gc-01

# Configure test data
./scripts/configure_test_data.sh test-gc-01
```

2. Test Scenarios:

```bash
# Full deployment test
pytest tests/integration/test_deployment_integration.py

# LoRa communication test
pytest tests/integration/test_lora_integration.py

# LaunchPad integration test
pytest tests/integration/test_launchpad_integration.py
```

3. Monitoring Tests:
```bash
# Test metrics collection
pytest tests/integration/test_monitoring.py

# Test alerting
pytest tests/integration/test_alerts.py
```

### Validation Steps

1. Deployment Validation:
- Verify service status
- Check system metrics
- Validate LoRa communication
- Test cloud connectivity

2. Data Flow Validation:
- Send test data packets
- Verify data processing
- Check cloud storage
- Validate monitoring metrics

3. Security Validation:
- Test access controls
- Verify encryption
- Check key management
- Validate secure communication

## Troubleshooting 🔍

### Common Issues

1. Deployment Failures:
```bash
# Check deployment logs
./scripts/logs.sh <station-id>

# Verify connectivity
./scripts/status.sh <station-id>

# Test configuration
./scripts/validate_config.sh <station-id>
```

2. Monitoring Issues:
```bash
# Check monitoring stack
./scripts/monitor.sh <station-id>

# Verify metrics
./scripts/check_metrics.sh <station-id>
```

3. Integration Issues:
```bash
# Validate integration
./scripts/test_integration.sh <station-id>

# Check cloud connectivity
./scripts/check_cloud.sh <station-id>
```

## Maintenance 🔧

### Regular Tasks

1. Updates:
```bash
# Update Ground Control
./scripts/update.sh <station-id>

# Update monitoring
./scripts/update.sh <station-id> --tags monitoring
```

2. Backups:
```bash
# Manual backup
./scripts/backup.sh <station-id>

# Verify backups
./scripts/verify_backup.sh <station-id>
```

3. Key Rotation:
```bash
# Generate new keys
./scripts/generate_keys.sh <deployment-id>

# Deploy new keys
./scripts/deploy.sh -e production -s <station-id> --tags security
```

## Contributing 🤝

1. Development Workflow:
- Create feature branch
- Implement changes
- Run tests
- Create pull request

2. Testing Requirements:
- Unit tests for new features
- Integration tests for components
- Documentation updates
- Security review

## Security Notes 🔒

1. Key Management:
- Never commit keys to repository
- Use secure key generation
- Follow key rotation schedule
- Maintain secure backups

2. Access Control:
- Use principle of least privilege
- Implement role-based access
- Monitor system access
- Regular security audits

## Support 💬

For support and questions:
- Create an issue in the repository
- Contact the SPLAT team
- Check documentation
- Review troubleshooting guide

## License 📄

MIT License - see LICENSE file for details.

---

Remember to replace placeholder values (`<station-id>`, `<ground-control-ip>`, etc.) with your actual deployment information.

For more detailed information, check the [documentation](docs/index.md).
