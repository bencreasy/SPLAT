"""
Error handling for Eden Control System.
Provides centralized error handling and reporting.
"""

import logging
import traceback
from typing import Dict, Any, Optional

# Configure logger
logger = logging.getLogger("Eden.ErrorHandler")

class EdenError(Exception):
    """Base exception class for Eden Control System"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(message)

class ConfigError(EdenError):
    """Configuration related errors"""
    pass

class HardwareError(EdenError):
    """Hardware related errors"""
    pass

class CommunicationError(EdenError):
    """Communication related errors"""
    pass

def handle_error(exception: Exception, component: str = "unknown", event_bus = None) -> None:
    """
    Central error handling function.
    Logs errors and publishes error events when appropriate.
    
    Args:
        exception: The exception to handle
        component: The component that raised the exception
        event_bus: Optional event bus to publish error events
    """
    error_type = type(exception).__name__
    
    # Get the full traceback
    tb = traceback.format_exc()
    
    # Log the error
    logger.error(f"Error in {component}: {str(exception)}")
    logger.debug(f"Traceback: {tb}")
    
    # If we have an event bus, publish an error event
    if event_bus:
        error_data = {
            "component": component,
            "type": error_type,
            "message": str(exception),
            "traceback": tb
        }
        
        # Add additional details if available
        if isinstance(exception, EdenError) and exception.details:
            error_data.update(exception.details)
            
        # Publish the error event
        event_bus.publish("system.error", error_data)
