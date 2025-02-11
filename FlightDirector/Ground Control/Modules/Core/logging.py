class LogManager:
    """
    Handles all system logging with different levels and targets.
    The system's record keeper.
    """
    def __init__(self, config: dict):
        self.config = config
        self.log_levels = {
            'DEBUG': 10,
            'INFO': 20,
            'WARNING': 30,
            'ERROR': 40,
            'CRITICAL': 50
        }
        
    async def log(self, level: str, message: str, **kwargs):
        """Log a message with the specified level"""
        timestamp = datetime.now().isoformat()
        log_entry = {
            'timestamp': timestamp,
            'level': level,
            'message': message,
            **kwargs
        }
        
        # Write to appropriate targets
        if self.config.get('file_logging', True):
            await self.write_to_file(log_entry)
            
        if self.config.get('cloud_logging', True):
            await self.send_to_cloud(log_entry)
