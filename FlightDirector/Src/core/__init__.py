# src/core/__init__.py

from .director import FlightDirector
from .events import EventBus, Event, EventType
from typing import Dict, Any

__version__ = "0.1.0"

__all__ = [
    "FlightDirector",
    "EventBus",
    "Event",
    "EventType",
]

def create_director(config_path: str) -> FlightDirector:
    """
    Factory function to create a new FlightDirector instance
    with proper initialization.
    """
    return FlightDirector(config_path)
