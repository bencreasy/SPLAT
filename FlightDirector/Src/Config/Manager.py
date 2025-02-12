# src/config/manager.py

import os
import yaml
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import jsonschema
from datetime import datetime

class ConfigError(Exception):
    """Base exception for configuration errors"""
    pass

class ConfigValidationError(ConfigError):
    """Configuration validation error"""
    pass

class ConfigNotFoundError(ConfigError):
    """Configuration file not found error"""
    pass

@dataclass
class ConfigSchema:
    """Configuration schema definition"""
    VERSION = "1.0.0"
    
    SCHEMA = {
        "type": "object",
        "required": [
            "environment",
            "gcp_project_id",
            "gcp_region",
            "deployment"
        ],
        "properties": {
            "environment": {
                "type": "string",
                "enum": ["development", "staging", "production"]
            },
            "gcp_project_id": {
                "type": "string",
                "pattern": "^[a-z][a-z0-9-]{4,28}[a-z0-9]$"
            },
            "gcp_region": {
                "type": "string"
            },
            "deployment": {
                "type": "object",
                "required": ["ansible_path", "key_storage_path"],
                "properties": {
                    "ansible_path": {"type": "string"},
                    "key_storage_path": {"type": "string"},
                    "monitoring_interval": {"type": "integer", "minimum": 30},
                    "backup_enabled": {"type": "boolean"}
                }
            },
            "ground_control": {
                "type": "object",
                "properties": {
                    "lora_frequency": {"type": "number"},
                    "lora_bandwidth": {"type": "integer"},
                    "spreading_factor": {"type": "integer"},
                    "tx_power": {"type": "integer"}
                }
            },
            "monitoring": {
                "type": "object",
                "properties": {
                    "enabled": {"type": "boolean"},
                    "log_level": {
                        "type": "string",
                        "enum": ["DEBUG", "INFO", "WARNING", "ERROR"]
                    }
                }
            }
        }
    }

class ConfigManager:
    """
    Manages configuration loading, validation, and updates for Flight Director
    """
    
    def __init__(self, config_path: str):
        self.config_path = Path(config_path)
        self.logger = logging.getLogger('FlightDirector.Config')
        self.config: Dict[str, Any] = {}
        self.environment_overrides: Dict[str, Any] = {}
        
    def load(self) -> Dict[str, Any]:
        """
        Load configuration from file and apply environment overrides
        """
        try:
            # Load base configuration
            self.config = self._load_yaml(self.config_path)
            
            # Load environment-specific overrides
            env_config_path = self.config_path.parent / f"{self.config['environment']}.yml"
            if env_config_path.exists():
                self.environment_overrides = self._load_yaml(env_config_path)
                self._merge_config()
            
            # Validate configuration
            self.validate_config(self.config)
            
            # Record load time
            self.config['_meta'] = {
                'loaded_at': datetime.utcnow().isoformat(),
                'version': ConfigSchema.VERSION
            }
            
            self.logger.info(f"Configuration loaded successfully for environment: {self.config['environment']}")
            return self.config
            
        except Exception as e:
            self.logger.error(f"Error loading configuration: {str(e)}")
            raise ConfigError(f"Failed to load configuration: {str(e)}")
    
    def save(self) -> None:
        """
        Save current configuration to file
        """
        try:
            # Create backup of existing config
            if self.config_path.exists():
                backup_path = self.config_path.parent / f"backup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.yml"
                self.config_path.rename(backup_path)
            
            # Save new configuration
            with open(self.config_path, 'w') as f:
                yaml.safe_dump(self.config, f)
            
            self.logger.info("Configuration saved successfully")
            
        except Exception as e:
            self.logger.error(f"Error saving configuration: {str(e)}")
            raise ConfigError(f"Failed to save configuration: {str(e)}")
    
    def update(self, updates: Dict[str, Any]) -> None:
        """
        Update configuration with new values
        """
        try:
            # Create temporary config with updates
            temp_config = self.config.copy()
            self._deep_update(temp_config, updates)
            
            # Validate updated configuration
            self.validate_config(temp_config)
            
            # Apply updates
            self.config = temp_config
            self.save()
            
            self.logger.info("Configuration updated successfully")
            
        except Exception as e:
            self.logger.error(f"Error updating configuration: {str(e)}")
            raise ConfigError(f"Failed to update configuration: {str(e)}")
    
    @staticmethod
    def validate_config(config: Dict[str, Any]) -> None:
        """
        Validate configuration against schema
        """
        try:
            jsonschema.validate(instance=config, schema=ConfigSchema.SCHEMA)
        except jsonschema.exceptions.ValidationError as e:
            raise ConfigValidationError(f"Configuration validation failed: {str(e)}")
    
    def get_deployment_config(self, deployment_id: str) -> Dict[str, Any]:
        """
        Get configuration for a specific deployment
        """
        deployment_config = self.config.get('deployment', {}).copy()
        deployment_config.update({
            'deployment_id': deployment_id,
            'environment': self.config['environment'],
            'gcp_project_id': self.config['gcp_project_id'],
            'gcp_region': self.config['gcp_region']
        })
        return deployment_config
    
    def _load_yaml(self, path: Path) -> Dict[str, Any]:
        """Load YAML configuration file"""
        if not path.exists():
            raise ConfigNotFoundError(f"Configuration file not found: {path}")
            
        with open(path, 'r') as f:
            return yaml.safe_load(f)
    
    def _merge_config(self) -> None:
        """Merge environment overrides into base configuration"""
        self._deep_update(self.config, self.environment_overrides)
    
    def _deep_update(self, base: Dict[str, Any], updates: Dict[str, Any]) -> None:
        """Recursively update nested dictionary"""
        for key, value in updates.items():
            if isinstance(value, dict) and key in base and isinstance(base[key], dict):
                self._deep_update(base[key], value)
            else:
                base[key] = value

def create_default_config(path: str, environment: str = "development") -> None:
    """
    Create a default configuration file
    """
    default_config = {
        "environment": environment,
        "gcp_project_id": "splat-project",
        "gcp_region": "us-central1",
        "deployment": {
            "ansible_path": "ansible",
            "key_storage_path": "keys",
            "monitoring_interval": 60,
            "backup_enabled": True
        },
        "ground_control": {
            "lora_frequency": 915.0,
            "lora_bandwidth": 125000,
            "spreading_factor": 7,
            "tx_power": 20
        },
        "monitoring": {
            "enabled": True,
            "log_level": "INFO"
        }
    }
    
    config_path = Path(path)
    if not config_path.exists():
        with open(config_path, 'w') as f:
            yaml.safe_dump(default_config, f)
