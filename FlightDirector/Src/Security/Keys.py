# src/security/keys.py

import os
import base64
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization

class KeyError(Exception):
    """Base exception for key-related errors"""
    pass

class KeyGenerationError(KeyError):
    """Key generation error"""
    pass

class KeyManager:
    """
    Manages encryption keys and credentials for Flight Director
    """
    
    def __init__(self, storage_path: str, encryption_enabled: bool = True):
        self.storage_path = Path(storage_path)
        self.encryption_enabled = encryption_enabled
        self.logger = logging.getLogger('FlightDirector.Security')
        self.fernet = None
        self._initialize_storage()
    
    def initialize(self) -> None:
        """
        Initialize key management system
        """
        try:
            if self.encryption_enabled:
                self._initialize_encryption()
            self.logger.info("Key management system initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize key management: {str(e)}")
            raise KeyError(f"Key management initialization failed: {str(e)}")
    
    def generate_deployment_keys(self, deployment_id: str) -> Dict[str, str]:
        """
        Generate necessary keys for a deployment
        """
        try:
            # Generate RSA key pair
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048
            )
            public_key = private_key.public_key()
            
            # Serialize keys
            private_pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )
            
            public_pem = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            
            # Store keys
            deployment_path = self._get_deployment_path(deployment_id)
            self._store_key(deployment_path / "private.pem", private_pem)
            self._store_key(deployment_path / "public.pem", public_pem)
            
            # Generate LaunchPad key
            launch_key = self._generate_launch_key(deployment_id, private_pem)
            self._store_key(deployment_path / "launchkey.json", 
                          json.dumps(launch_key).encode())
            
            self.logger.info(f"Generated deployment keys for {deployment_id}")
            return {
                "private_key": deployment_path / "private.pem",
                "public_key": deployment_path / "public.pem",
                "launch_key": deployment_path / "launchkey.json"
            }
            
        except Exception as e:
            self.logger.error(f"Failed to generate deployment keys: {str(e)}")
            raise KeyGenerationError(f"Key generation failed: {str(e)}")
    
    def get_deployment_keys(self, deployment_id: str) -> Dict[str, bytes]:
        """
        Retrieve keys for a deployment
        """
        try:
            deployment_path = self._get_deployment_path(deployment_id)
            
            if not deployment_path.exists():
                raise KeyError(f"No keys found for deployment {deployment_id}")
            
            keys = {}
            for key_file in ["private.pem", "public.pem", "launchkey.json"]:
                key_path = deployment_path / key_
