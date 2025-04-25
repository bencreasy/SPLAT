import logging
import pygame
from datetime import datetime
from typing import Dict, Any, List, Tuple

class Dashboard:
    """
    Main dashboard view for Eden Control System.
    Displays system status and key metrics.
    """
    def __init__(self, config_manager, event_bus):
        self.logger = logging.getLogger("Eden.Dashboard")
        self.config = config_manager
        self.event_bus = event_bus
        
        # Display elements
        self.title_font = None
        self.text_font = None
        self.status_font = None
        
        # System status
        self.system_status = "Initializing"
        self.cloud_status = "Disconnected"
        self.last_update = datetime.now()
        self.messages = []
        
        # Subscribe to events
        if self.event_bus:
            self.event_bus.subscribe("system.status", self._handle_status_event)
            self.event_bus.subscribe("cloud.status", self._handle_cloud_event)
            self.event_bus.subscribe("system.message", self._handle_message_event)
            
        self.logger.debug("Dashboard initialized")
        
    def initialize(self):
        """Initialize dashboard resources"""
        try:
            self.title_font = pygame.font.SysFont(None, 36)
            self.text_font = pygame.font.SysFont(None, 24)
            self.status_font = pygame.font.SysFont(None, 28)
            self.logger.debug("Dashboard resources initialized")
            
        except Exception as e:
            self.logger.error(f"Error initializing dashboard: {str(e)}")
            
    def render(self, surface):
        """Render the dashboard view"""
        try:
            # Make sure resources are initialized
            if not self.title_font:
                self.initialize()
                
            # Get surface dimensions
            width, height = surface.get_size()
            
            # Render title
            title = self.title_font.render("Eden Control System", True, (255, 255, 255))
            surface.blit(title, (width//2 - title.get_width()//2, 20))
            
            # Render current time
            time_text = self.text_font.render(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), True, (200, 200, 200))
            surface.blit(time_text, (width - time_text.get_width() - 20, 20))
            
            # Render system status
            status_color = (0, 255, 0) if self.system_status == "Online" else (255, 165, 0)
            status_text = self.status_font.render(f"System: {self.system_status}", True, status_color)
            surface.blit(status_text, (30, 80))
            
            # Render cloud status
            cloud_color = (0, 255, 0) if self.cloud_status == "Connected" else (255, 165, 0)
            cloud_text = self.status_font.render(f"Cloud: {self.cloud_status}", True, cloud_color)
            surface.blit(cloud_text, (30, 120))
            
            # Render last update time
            update_text = self.text_font.render(f"Last Update: {self.last_update.strftime('%H:%M:%S')}", True, (200, 200, 200))
            surface.blit(update_text, (30, 160))
            
            # Render message history
            message_y = 220
            message_header = self.text_font.render("Recent Messages:", True, (255, 255, 255))
            surface.blit(message_header, (30, message_y))
            message_y += 30
            
            for i, message in enumerate(self.messages[-5:]):  # Show last 5 messages
                msg_text = self.text_font.render(message, True, (200, 200, 200))
                surface.blit(msg_text, (40, message_y + i * 30))
                
        except Exception as e:
            self.logger.error(f"Error rendering dashboard: {str(e)}")
            
    def handle_touch(self, pos: Tuple[int, int]):
        """Handle touch events on the dashboard"""
        # Example: Register touch zones here
        pass
        
    def _handle_status_event(self, event):
        """Handle system status events"""
        try:
            data = event.get("data", {})
            if "status" in data:
                self.system_status = data["status"]
                self.last_update = datetime.now()
                
        except Exception as e:
            self.logger.error(f"Error handling status event: {str(e)}")
            
    def _handle_cloud_event(self, event):
        """Handle cloud status events"""
        try:
            data = event.get("data", {})
            if "status" in data:
                self.cloud_status = data["status"]
                self.last_update = datetime.now()
                
        except Exception as e:
            self.logger.error(f"Error handling cloud event: {str(e)}")
            
    def _handle_message_event(self, event):
        """Handle system message events"""
        try:
            data = event.get("data", {})
            if "message" in data:
                self.messages.append(f"{datetime.now().strftime('%H:%M:%S')} - {data['message']}")
                # Keep only last 20 messages
                if len(self.messages) > 20:
                    self.messages = self.messages[-20:]
                    
        except Exception as e:
            self.logger.error(f"Error handling message event: {str(e)}")
