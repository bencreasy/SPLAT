import os
import yaml
import logging
from typing import Dict, Any, Optional

class ConfigManager:
    """
    Configuration management for Eden Control System.
    Handles loading and accessing configuration.
    """
    def __init__(self, config_path: str = "config/default.yml"):
        self.logger = logging.getLogger("Eden.ConfigManager")
        self.config_path = config_path
        self.config = {}
        self.logger.debug("ConfigManager initialized")
        
    def load(self) -> bool:
        """Load configuration from file"""
        try:
            if not os.path.exists(self.config_path):
                self.logger.warning(f"Config file not found: {self.config_path}")
                return False
                
            with open(self.config_path, 'r') as f:
                self.config = yaml.safe_load(f)
                
            self.logger.info(f"Loaded configuration from {self.config_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error loading configuration: {str(e)}")
            return False
            
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value by key"""
        # Handle nested keys with dot notation
        if '.' in key:
            parts = key.split('.')
            value = self.config
            for part in parts:
                if isinstance(value, dict) and part in value:
                    value = value[part]
                else:
                    return default
            return value
        else:
            return self.config.get(key, default)
            
    def get_section(self, section: str) -> Dict:
        """Get an entire configuration section"""
        return self.config.get(section, {})
