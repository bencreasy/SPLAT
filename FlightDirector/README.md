# SPLAT Flight Director 🛩️

Flight Director is the automation and orchestration system for SPLAT (Soil Permeability & Logging Analysis Transponder) deployments. It manages the deployment, configuration, and monitoring of Ground Control stations and LaunchPad infrastructure.

## Project Structure 📁

```
flight-director/
├── src/
│   ├── core/
│   │   ├── __init__.py
│   │   ├── director.py        # Core Flight Director class
│   │   └── events.py         # Event system
│   │
│   ├── ansible/
│   │   ├── __init__.py
│   │   ├── deployment.py     # Ansible automation
│   │   └── playbooks/
│   │       ├── site.yml
│   │       ├── ground_control.yml
│   │       └── launchpad.yml
│   │
│   ├── config/
│   │   ├── __init__.py
│   │   └── manager.py        # Configuration management
│   │
│   └── security/
│       ├── __init__.py
│       └── keys.py           # Key management
│
├── config/
│   ├── default.yml           # Default configuration
│   ├── development.yml       # Development environment
│   └── production.yml        # Production environment
│
├── ansible/
│   ├── inventory/
│   │   └── ground_control.yml
│   │
│   ├── roles/
│   │   ├── common/
│   │   ├── docker/
│   │   ├── ground_control/
│   │   ├── launchpad/
│   │   └── monitoring/
│   │
│   └── vars/
│       ├── main.yml
│       └── vault.yml
│
├── scripts/
│   ├── install.sh           # Installation script
│   ├── deploy.sh            # Deployment script
│   └── generate_keys.sh     # Key generation utilities
│
├── tests/
│   ├── unit/
│   │   └── test_director.py
│   └── integration/
│       └── test_deployment.py
│
└── keys/                    # Secure key storage (gitignored)
    ├── encryption.key
    └── deployments/
```

## Prerequisites 🛠️

- Python 3.9+
- Ansible 2.9+
- Docker
- Git
- GCP Account with required permissions

## Installation 🚀

1. Clone the repository:
```bash
git clone https://github.com/your-org/splat-flight-director.git
cd splat-flight-director
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Initialize configuration:
```bash
cp config/default.yml config/development.yml
# Edit development.yml with your settings
```

5. Generate encryption keys:
```bash
./scripts/generate_keys.sh
```

## Configuration 📝

### Environment Configuration

Create appropriate config files in `config/` directory:
- `development.yml`: Development environment settings
- `staging.yml`: Staging environment settings
- `production.yml`: Production environment settings

Example configuration:
```yaml
# config/development.yml
environment: development
gcp_project_id: splat-dev-xxxxx
gcp_region: us-central1

ansible:
  playbook_path: ansible/playbooks/site.yml
  inventory_path: ansible/inventory/ground_control.yml

key_storage_path: keys/deployments
```

### Ansible Configuration

1. Update inventory file:
```yaml
# ansible/inventory/ground_control.yml
all:
  children:
    ground_control:
      hosts:
        gc-001:
          ansible_host: 192.168.1.100
          ansible_user: pi
```

2. Configure vault (for sensitive data):
```bash
ansible-vault create ansible/vars/vault.yml
```

## Usage 💻

### Deploying Ground Control Station

```python
from flight_director.core.director import FlightDirector
from flight_director.ansible.deployment import AnsibleDeployment

# Initialize Flight Director
director = FlightDirector('config/development.yml')

# Configure station
station_config = {
    'station_id': 'gc-001',
    'deployment_id': 'splat-dev-001',
    'ip_address': '192.168.1.100',
    'ssh_user': 'pi'
}

# Deploy station
await director.deploy_ground_station(station_config)
```

### Managing Deployments

1. Register new station:
```python
station_id = await director.register_ground_station(station_config)
```

2. Deploy LaunchPad:
```python
success = await director.deploy_launchpad(station_id)
```

3. Monitor deployment:
```python
status = await director.get_deployment_status(station_id)
```

## Development 🔧

### Running Tests

```bash
# Run all tests
pytest tests/

# Run specific test category
pytest tests/unit/
pytest tests/integration/
```

### Adding New Features

1. Create feature branch:
```bash
git checkout -b feature/new-feature
```

2. Implement feature and tests

3. Update documentation

4. Create pull request

## Security 🔒

### Key Management

- All keys are stored in `keys/` directory (gitignored)
- Encryption key is required for accessing deployment keys
- Use `scripts/generate_keys.sh` to create new keys

### Sensitive Data

- Use Ansible Vault for sensitive variables
- Encrypt all credential files
- Never commit unencrypted keys or credentials

## Troubleshooting 🔍

Common issues and solutions:

1. Deployment Failures
- Check SSH connectivity
- Verify Ansible inventory
- Check system requirements
- Review logs in `logs/ansible.log`

2. Key Management Issues
- Regenerate encryption key
- Verify key permissions
- Check key storage path

## Contributing 🤝

1. Fork the repository
2. Create feature branch
3. Commit changes
4. Create pull request

## License 📄

MIT License - see LICENSE file for details

---

## Quick Reference 📚

### Common Commands

```bash
# Start new deployment
./scripts/deploy.sh -s <station_id> -e <environment>

# Generate new keys
./scripts/generate_keys.sh -d <deployment_id>

# Check deployment status
./scripts/status.sh -s <station_id>
```

### Configuration Templates

See `config/default.yml` for all available configuration options.

### Directory Permissions

```bash
# Set correct permissions
chmod 700 keys/
chmod 600 keys/encryption.key
chmod 600 keys/deployments/*
```

For more detailed information, check the [documentation](docs/index.md).
