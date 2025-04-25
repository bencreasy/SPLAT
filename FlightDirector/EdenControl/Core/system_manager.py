import logging
import time
from threading import Thread

class SystemManager:
    """
    Main system coordinator for Eden control system.
    Handles initialization, startup, and shutdown.
    """
    def __init__(self, config_path="config/default.yml", event_bus=None):
        self.logger = logging.getLogger("Eden.SystemManager")
        self.config_path = config_path
        self.event_bus = event_bus
        self.running = False
        self.components = {}
        self.logger.info("System Manager initialized")
        
    def register_component(self, name, component):
        """Register a component with the system manager"""
        self.components[name] = component
        self.logger.debug(f"Registered component: {name}")
        
    def start(self):
        """Start the system and all registered components"""
        self.logger.info("Starting Eden Control System")
        self.running = True
        
        # Start components in dependency order
        for name, component in self.components.items():
            try:
                if hasattr(component, 'start'):
                    self.logger.debug(f"Starting component: {name}")
                    component.start()
            except Exception as e:
                self.logger.error(f"Error starting component {name}: {str(e)}")
                
        # Publish system started event
        if self.event_bus:
            self.event_bus.publish("system.started", {"timestamp": time.time()})
            
        self.logger.info("Eden Control System started")
        
    def stop(self):
        """Stop the system and all registered components"""
        self.logger.info("Stopping Eden Control System")
        self.running = False
        
        # Stop components in reverse order
        for name, component in reversed(list(self.components.items())):
            try:
                if hasattr(component, 'stop'):
                    self.logger.debug(f"Stopping component: {name}")
                    component.stop()
            except Exception as e:
                self.logger.error(f"Error stopping component {name}: {str(e)}")
                
        # Publish system stopped event
        if self.event_bus:
            self.event_bus.publish("system.stopped", {"timestamp": time.time()})
            
        self.logger.info("Eden Control System stopped")
