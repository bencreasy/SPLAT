# src/ansible/__init__.py

from .deployment import AnsibleDeployment, DeploymentConfig, DeploymentStatus, AnsibleError

__all__ = [
    "AnsibleDeployment",
    "DeploymentConfig",
    "DeploymentStatus",
    "AnsibleError"
]

# Version of the Ansible module
__version__ = "0.1.0"

# Default paths
DEFAULT_INVENTORY_PATH = "ansible/inventory"
DEFAULT_PLAYBOOK_PATH = "ansible/playbooks"
DEFAULT_ROLES_PATH = "ansible/roles"
DEFAULT_VARS_PATH = "ansible/vars"

class AnsibleError(Exception):
    """Base exception for Ansible-related errors"""
    pass

class AnsibleConfigError(AnsibleError):
    """Configuration-related errors"""
    pass

class AnsibleExecutionError(AnsibleError):
    """Execution-related errors"""
    pass
