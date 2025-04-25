import logging
import threading
import time
import pygame
from typing import Dict, Any, Optional, Tuple

class DisplayManager:
    """
    Manages the touchscreen display for Eden Control System.
    Handles initialization and rendering.
    """
    def __init__(self, config_manager, event_bus):
        self.logger = logging.getLogger("Eden.DisplayManager")
        self.config = config_manager
        self.event_bus = event_bus
        self.running = False
        self.render_thread = None
        
        # Display settings
        self.width = self.config.get("display.width", 800)
        self.height = self.config.get("display.height", 480)
        self.fps = self.config.get("display.fps", 30)
        
        # Pygame objects
        self.screen = None
        self.clock = None
        self.font = None
        
        # Current view
        self.current_view = None
        self.views = {}
        
        # Touch handling
        self.touch_handlers = []
        
        self.logger.debug("DisplayManager initialized")
        
    def register_view(self, name: str, view):
        """Register a view with the display manager"""
        self.views[name] = view
        self.logger.debug(f"Registered view: {name}")
        
    def register_touch_handler(self, handler):
        """Register a touch event handler"""
        self.touch_handlers.append(handler)
        
    def set_view(self, name: str):
        """Set the current view"""
        if name in self.views:
            self.current_view = self.views[name]
            self.logger.debug(f"Set current view: {name}")
        else:
            self.logger.warning(f"View not found: {name}")
        
    def start(self):
        """Initialize and start the display"""
        try:
            # Initialize pygame
            pygame.init()
            pygame.display.set_caption("Eden Control System")
            
            # Set up display
            self.screen = pygame.display.set_mode((self.width, self.height))
            self.clock = pygame.time.Clock()
            self.font = pygame.font.SysFont(None, 24)
            
            self.running = True
            self.render_thread = threading.Thread(target=self._render_loop, daemon=True)
            self.render_thread.start()
            
            self.logger.info("DisplayManager started")
            
        except Exception as e:
            self.logger.error(f"Error starting display: {str(e)}")
            
    def stop(self):
        """Stop the display"""
        self.running = False
        if self.render_thread:
            self.render_thread.join(timeout=5.0)
            
        # Clean up pygame
        pygame.quit()
        self.logger.info("DisplayManager stopped")
        
    def _render_loop(self):
        """Main rendering loop"""
        while self.running:
            try:
                # Handle events
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.running = False
                    elif event.type == pygame.MOUSEBUTTONDOWN:
                        self._handle_touch(event.pos)
                
                # Clear screen
                self.screen.fill((0, 0, 0))
                
                # Render current view
                if self.current_view:
                    self.current_view.render(self.screen)
                else:
                    # Render default text
                    text = self.font.render("Eden Control System", True, (255, 255, 255))
                    self.screen.blit(text, (self.width//2 - text.get_width()//2, self.height//2))
                
                # Update display
                pygame.display.flip()
                
                # Control frame rate
                self.clock.tick(self.fps)
                
            except Exception as e:
                self.logger.error(f"Error in render loop: {str(e)}")
                time.sleep(1)
                
    def _handle_touch(self, pos: Tuple[int, int]):
        """Handle touch events"""
        # Notify current view
        if self.current_view and hasattr(self.current_view, 'handle_touch'):
            self.current_view.handle_touch(pos)
            
        # Notify registered handlers
        for handler in self.touch_handlers:
            try:
                handler(pos)
            except Exception as e:
                self.logger.error(f"Error in touch handler: {str(e)}")
                
        # Publish touch event
        if self.event_bus:
            self.event_bus.publish("display.touch", {"position": pos})
