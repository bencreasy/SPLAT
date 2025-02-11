class SystemManager:
    """
    Manages the overall system lifecycle and module coordination.
    Think of it as the conductor of an orchestra.
    """
    def __init__(self):
        self.modules = {}
        self.status = "initialized"
        self.event_bus = EventBus()
        self.config = ConfigManager()
        
    async def start(self):
        """Start all modules in the correct order"""
        try:
            # Load configuration
            await self.config.load()
            
            # Start modules in dependency order
            for module_name in self.config.get_module_order():
                if self.config.is_module_enabled(module_name):
                    await self.start_module(module_name)
                    
            self.status = "running"
            
        except Exception as e:
            self.status = "error"
            raise SystemStartError(f"Failed to start: {str(e)}")
            
    async def stop(self):
        """Gracefully stop all modules"""
        self.status = "stopping"
        
        # Stop in reverse order
        for module_name in reversed(self.modules.keys()):
            await self.stop_module(module_name)
            
        self.status = "stopped"
