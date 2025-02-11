class GCError(Exception):
    """Base class for Ground Control errors"""
    def __init__(self, message: str, code: int = None):
        self.message = message
        self.code = code
        self.timestamp = datetime.now()
        super().__init__(self.message)

class SystemStartError(GCError):
    """Raised when system fails to start"""
    pass

class ConfigError(GCError):
    """Configuration related errors"""
    pass

class ModuleError(GCError):
    """Module specific errors"""
    pass

async def error_handler(error: Exception, context: dict = None):
    """Central error handling function"""
    error_data = {
        'type': type(error).__name__,
        'message': str(error),
        'timestamp': datetime.now().isoformat(),
        'context': context or {}
    }
    
    # Log the error
    await log_manager.log('ERROR', error_data)
    
    # Notify monitoring system
    await event_bus.publish(Event(
        type='error',
        source='error_handler',
        data=error_data
    ))
