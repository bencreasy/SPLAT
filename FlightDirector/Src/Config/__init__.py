# src/config/__init__.py

from .manager import ConfigManager, ConfigError, ConfigValidationError
from typing import Dict, Any

__version__ = "0.1.0"

__all__ = [
    "ConfigManager",
    "ConfigError",
    "ConfigValidationError",
    "load_config",
    "validate_config"
]

def load_config(config_path: str) -> Dict[str, Any]:
    """Helper function to load configuration"""
    manager = ConfigManager(config_path)
    return manager.load()

def validate_config(config: Dict[str, Any]) -> bool:
    """Helper function to validate configuration"""
    try:
        ConfigManager.validate_config(config)
        return True
    except ConfigValidationError:
        return False
