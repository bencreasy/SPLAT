import logging
import json
import time
import threading
import requests
from typing import Dict, Any, Optional

class CloudManager:
    """
    Manages communication with the LaunchPad cloud system.
    Handles data synchronization and command receiving.
    """
    def __init__(self, config_manager, event_bus):
        self.logger = logging.getLogger("Eden.CloudManager")
        self.config = config_manager
        self.event_bus = event_bus
        self.running = False
        self.sync_thread = None
        self.api_url = self.config.get("cloud.api_url", "https://api.example.com/v1")
        self.api_key = self.config.get("cloud.api_key", "")
        self.system_id = self.config.get("system.id", "eden-prototype")
        self.sync_interval = self.config.get("cloud.sync_interval", 60)
        
        # Subscribe to system events
        if self.event_bus:
            self.event_bus.subscribe("system.status", self._handle_status_event)
        
        self.logger.debug("CloudManager initialized")
        
    def start(self):
        """Start cloud communication"""
        self.running = True
        self.sync_thread = threading.Thread(target=self._sync_loop, daemon=True)
        self.sync_thread.start()
        self.logger.info("CloudManager started")
        
        # Send initial hello message
        self.send_hello()
        
    def stop(self):
        """Stop cloud communication"""
        self.running = False
        if self.sync_thread:
            self.sync_thread.join(timeout=5.0)
        self.logger.info("CloudManager stopped")
        
    def send_hello(self):
        """Send hello message to LaunchPad"""
        message = {
            "type": "hello",
            "system_id": self.system_id,
            "timestamp": time.time(),
            "version": "0.1.0",
            "status": "online"
        }
        self._send_to_cloud(message)
        
    def _send_to_cloud(self, data: Dict[str, Any]) -> bool:
        """Send data to the cloud API"""
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            response = requests.post(
                f"{self.api_url}/telemetry", 
                json=data,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                self.logger.debug(f"Successfully sent data to cloud")
                return True
            else:
                self.logger.warning(f"Failed to send data to cloud: {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error sending data to cloud: {str(e)}")
            return False
            
    def _sync_loop(self):
        """Background thread for periodic synchronization"""
        while self.running:
            try:
                # Get commands from cloud
                self._check_commands()
                
                # Sleep until next sync
                time.sleep(self.sync_interval)
                
            except Exception as e:
                self.logger.error(f"Error in sync loop: {str(e)}")
                time.sleep(10)  # Shorter interval on error
                
    def _check_commands(self):
        """Check for commands from LaunchPad"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}"
            }
            response = requests.get(
                f"{self.api_url}/commands?system_id={self.system_id}",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                commands = response.json()
                if commands and isinstance(commands, list):
                    for command in commands:
                        self._process_command(command)
            else:
                self.logger.warning(f"Failed to check commands: {response.status_code}")
                
        except Exception as e:
            self.logger.error(f"Error checking commands: {str(e)}")
            
    def _process_command(self, command: Dict[str, Any]):
        """Process a command from LaunchPad"""
        try:
            command_type = command.get("type")
            if not command_type:
                return
                
            # Publish command event
            self.event_bus.publish(f"command.{command_type}", command)
            self.logger.info(f"Received command: {command_type}")
            
        except Exception as e:
            self.logger.error(f"Error processing command: {str(e)}")
            
    def _handle_status_event(self, event):
        """Handle system status events"""
        try:
            # Send status update to cloud
            data = event.get("data", {})
            data["system_id"] = self.system_id
            data["type"] = "status"
            data["timestamp"] = time.time()
            
            self._send_to_cloud(data)
            
        except Exception as e:
            self.logger.error(f"Error handling status event: {str(e)}")
