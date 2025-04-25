import logging
import os
from datetime import datetime
import json
from typing import Dict, Any, List, Optional

class LogManager:
    """
    Manages logging for Eden Control System.
    Handles file-based and structured logging.
    """
    def __init__(self, config_manager, event_bus=None):
        self.logger = logging.getLogger("Eden.LogManager")
        self.config = config_manager
        self.event_bus = event_bus
        
        # Log settings
        self.log_dir = self.config.get("logging.directory", "logs")
        self.max_size = self.config.get("logging.max_size", 10 * 1024 * 1024)  # 10MB
        self.backup_count = self.config.get("logging.backup_count", 5)
        
        # Ensure log directory exists
        os.makedirs(self.log_dir, exist_ok=True)
        
        # Subscribe to events for logging
        if self.event_bus:
            self.event_bus.subscribe("system.log", self._handle_log_event)
            
        self.logger.debug("LogManager initialized")
        
    def start(self):
        """Start the log manager"""
        # Configure file-based logging
        self._configure_logging()
        self.logger.info("LogManager started")
        
    def stop(self):
        """Stop the log manager"""
        self.logger.info("LogManager stopped")
        
    def log_event(self, event_type: str, data: Dict[str, Any]):
        """Log a structured event"""
        try:
            timestamp = datetime.now().isoformat()
            
            # Create log entry
            log_entry = {
                "timestamp": timestamp,
                "type": event_type,
                "data": data
            }
            
            # Log to file
            with open(os.path.join(self.log_dir, "events.log"), "a") as f:
                f.write(json.dumps(log_entry) + "\n")
                
            self.logger.debug(f"Logged event: {event_type}")
            
        except Exception as e:
            self.logger.error(f"Error logging event: {str(e)}")
            
    def _configure_logging(self):
        """Configure Python logging"""
        try:
            from logging.handlers import RotatingFileHandler
            
            # Create root logger
            root_logger = logging.getLogger()
            level = getattr(logging, self.config.get("logging.level", "INFO"))
            root_logger.setLevel(level)
            
            # Create console handler
            console = logging.StreamHandler()
            console.setLevel(level)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            console.setFormatter(formatter)
            root_logger.addHandler(console)
            
            # Create file handler
            log_file = os.path.join(self.log_dir, "eden.log")
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=self.max_size,
                backupCount=self.backup_count
            )
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
            
            self.logger.debug(f"Logging configured to file: {log_file}")
            
        except Exception as e:
            self.logger.error(f"Error configuring logging: {str(e)}")
            
    def _handle_log_event(self, event):
        """Handle log events from the event bus"""
        try:
            data = event.get("data", {})
            if "message" in data and "level" in data:
                level = getattr(logging, data["level"], logging.INFO)
                self.logger.log(level, data["message"])
                
        except Exception as e:
            self.logger.error(f"Error handling log event: {str(e)}")
