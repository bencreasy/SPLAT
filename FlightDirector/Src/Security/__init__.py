# src/security/__init__.py

from .keys import KeyManager, KeyError, KeyGenerationError
from typing import Dict, Any

__version__ = "0.1.0"

__all__ = [
    "KeyManager",
    "KeyError",
    "KeyGenerationError",
    "initialize_security",
    "create_key_manager"
]

def initialize_security(config: Dict[str, Any]) -> None:
    """Initialize security components"""
    key_manager = create_key_manager(config)
    key_manager.initialize()

def create_key_manager(config: Dict[str, Any]) -> KeyManager:
    """Create and configure key manager instance"""
    return KeyManager(
        storage_path=config['deployment']['key_storage_path'],
        encryption_enabled=True
    )
