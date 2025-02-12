# src/core/events.py

from dataclasses import dataclass
from datetime import datetime
from enum import Enum, auto
from typing import Any, Dict, List, Callable, Optional
import asyncio
import logging

class EventType(Enum):
    """Enumeration of all possible event types in Flight Director"""
    
    # Station Events
    STATION_REGISTERED = auto()
    STATION_DEPLOYED = auto()
    STATION_UPDATED = auto()
    STATION_ERROR = auto()
    
    # Node Events
    NODE_REGISTERED = auto()
    NODE_ASSIGNED = auto()
    NODE_STATUS_UPDATE = auto()
    NODE_ERROR = auto()
    
    # Deployment Events
    DEPLOYMENT_STARTED = auto()
    DEPLOYMENT_COMPLETE = auto()
    DEPLOYMENT_FAILED = auto()
    
    # LaunchPad Events
    LAUNCHPAD_DEPLOYED = auto()
    LAUNCHPAD_UPDATED = auto()
    LAUNCHPAD_ERROR = auto()
    
    # System Events
    CONFIG_UPDATED = auto()
    HEALTH_CHECK = auto()
    SYSTEM_ERROR = auto()

@dataclass
class Event:
    """
    Represents an event in the Flight Director system
    """
    type: EventType
    source: str
    data: Dict[str, Any]
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()

class EventBus:
    """
    Event bus for handling system-wide events in Flight Director
    """
    
    def __init__(self):
        self.subscribers: Dict[EventType, List[Callable]] = {}
        self.logger = logging.getLogger('FlightDirector.Events')
        self.queue = asyncio.Queue()
        self._running = False
    
    def subscribe(self, event_type: EventType, callback: Callable[[Event], None]) -> None:
        """
        Subscribe to events of a specific type
        """
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(callback)
        self.logger.debug(f"Subscribed to {event_type} events")
    
    def unsubscribe(self, event_type: EventType, callback: Callable[[Event], None]) -> None:
        """
        Unsubscribe from events of a specific type
        """
        if event_type in self.subscribers and callback in self.subscribers[event_type]:
            self.subscribers[event_type].remove(callback)
            self.logger.debug(f"Unsubscribed from {event_type} events")
    
    async def publish(self, event: Event) -> None:
        """
        Publish an event to all subscribers
        """
        await self.queue.put(event)
        self.logger.debug(f"Published event: {event.type}")
    
    async def start(self) -> None:
        """
        Start the event processing loop
        """
        self._running = True
        self.logger.info("Event bus started")
        
        while self._running:
            try:
                event = await self.queue.get()
                await self._process_event(event)
                self.queue.task_done()
            except Exception as e:
                self.logger.error(f"Error processing event: {str(e)}")
    
    async def stop(self) -> None:
        """
        Stop the event processing loop
        """
        self._running = False
        self.logger.info("Event bus stopped")
    
    async def _process_event(self, event: Event) -> None:
        """
        Process a single event
        """
        if event.type in self.subscribers:
            for callback in self.subscribers[event.type]:
                try:
                    await self._execute_callback(callback, event)
                except Exception as e:
                    self.logger.error(f"Error in event callback: {str(e)}")
    
    async def _execute_callback(self, callback: Callable[[Event], None], event: Event) -> None:
        """
        Execute a callback function, handling both async and sync callbacks
        """
        try:
            if asyncio.iscoroutinefunction(callback):
                await callback(event)
            else:
                callback(event)
        except Exception as e:
            self.logger.error(f"Error executing callback: {str(e)}")
            raise

class EventLogger:
    """
    Logger for system events
    """
    
    def __init__(self, event_bus: EventBus):
        self.logger = logging.getLogger('FlightDirector.EventLogger')
        event_bus.subscribe(EventType.SYSTEM_ERROR, self._log_system_error)
        event_bus.subscribe(EventType.DEPLOYMENT_FAILED, self._log_deployment_error)
        
    async def _log_system_error(self, event: Event) -> None:
        """Log system errors"""
        self.logger.error(f"System Error: {event.data.get('message', 'Unknown error')}")
        self.logger.debug(f"Error details: {event.data}")
    
    async def _log_deployment_error(self, event: Event) -> None:
        """Log deployment errors"""
        self.logger.error(f"Deployment Error: {event.data.get('message', 'Unknown error')}")
        self.logger.debug(f"Deployment details: {event.data}")

def setup_event_logging(log_level: str = 'INFO') -> None:
    """
    Configure event logging system
    """
    logger = logging.getLogger('FlightDirector')
    logger.setLevel(getattr(logging, log_level))
    
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
