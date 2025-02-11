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
