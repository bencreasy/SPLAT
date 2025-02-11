# Ground Control Core Module

## Directory Structure
```
modules/core/
├── __init__.py
├── system.py       # System management and lifecycle
├── config.py       # Configuration handling
├── events.py       # Event system
├── logging.py      # Logging system
└── errors.py       # Error handling
```

## Core Components

### 1. System Manager (system.py)
```python
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
```

### 2. Configuration Manager (config.py)
```python
class ConfigManager:
    """
    Handles all configuration loading and access.
    Single source of truth for system settings.
    """
    def __init__(self):
        self.config = {}
        self.secrets = {}
        self.module_configs = {}
        
    async def load(self):
        """Load all configuration files"""
        # Load main config
        self.config = await self.load_yaml('config/default.yml')
        
        # Load module configs
        self.module_configs = await self.load_yaml('config/modules.yml')
        
        # Load secrets (encrypted)
        self.secrets = await self.load_secrets('config/secrets.yml.enc')
        
    def get_module_config(self, module_name: str) -> dict:
        """Get configuration for specific module"""
        return self.module_configs.get(module_name, {})
        
    def get_secret(self, key: str) -> str:
        """Safely retrieve encrypted secrets"""
        if key not in self.secrets:
            raise ConfigError(f"Secret {key} not found")
        return self.secrets[key]
```

### 3. Event System (events.py)
```python
from dataclasses import dataclass
from typing import Any, Dict
from datetime import datetime

@dataclass
class Event:
    """
    Standard event format for all system communication.
    Like an internal envelope for messages.
    """
    type: str           # What kind of event
    source: str         # Who sent it
    data: Dict[str, Any]  # The actual information
    timestamp: datetime  # When it happened
    priority: int = 1   # How important (1-5)

class EventBus:
    """
    Central event distribution system.
    Think of it as the system's nervous system.
    """
    def __init__(self):
        self.subscribers = {}
        self.event_history = []
        
    def subscribe(self, event_type: str, callback, priority: bool = False):
        """Subscribe to specific event types"""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append({
            'callback': callback,
            'priority': priority
        })
        
    async def publish(self, event: Event):
        """Distribute events to subscribers"""
        if event.type in self.subscribers:
            # Handle priority subscribers first
            subscribers = sorted(
                self.subscribers[event.type],
                key=lambda x: x['priority'],
                reverse=True
            )
            
            for subscriber in subscribers:
                try:
                    await subscriber['callback'](event)
                except Exception as e:
                    await self.handle_error(e, event)
```

### 4. Logging System (logging.py)
```python
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
```

### 5. Error Handling (errors.py)
```python
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
```

## Usage Example

```python
# Example of how modules interact with core
async def main():
    # Initialize core systems
    system = SystemManager()
    
    # Configure event handling
    system.event_bus.subscribe('module_error', error_handler)
    
    # Start the system
    try:
        await system.start()
        
        # Example event publication
        await system.event_bus.publish(Event(
            type='status_update',
            source='main',
            data={'status': 'running'}
        ))
        
    except Exception as e:
        await error_handler(e)
        await system.stop()
```

## Key Features

1. Clean Module Interface:
   - Event-based communication
   - Standard configuration access
   - Consistent error handling
   - Robust logging

2. Error Recovery:
   - Graceful degradation
   - Auto-restart capabilities
   - Error reporting
   - State preservation

3. Configuration Management:
   - Secure secrets handling
   - Module-specific configs
   - Runtime updates
   - Validation

4. Logging and Monitoring:
   - Multi-level logging
   - Performance tracking
   - Event history
   - Debug support
