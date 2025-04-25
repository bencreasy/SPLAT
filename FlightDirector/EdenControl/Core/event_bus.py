import logging
import threading
import queue
import time
from typing import Dict, List, Callable, Any

class EventBus:
    """
    Simple event distribution system for Eden Control.
    Handles publishing events and distributing to subscribers.
    """
    def __init__(self):
        self.logger = logging.getLogger("Eden.EventBus")
        self.subscribers = {}
        self.event_queue = queue.Queue()
        self.running = False
        self.worker_thread = None
        self.logger.debug("EventBus initialized")
        
    def subscribe(self, event_type: str, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Subscribe to events of a specific type"""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(callback)
        self.logger.debug(f"Subscribed to event: {event_type}")
        
    def unsubscribe(self, event_type: str, callback: Callable) -> None:
        """Unsubscribe from events of a specific type"""
        if event_type in self.subscribers and callback in self.subscribers[event_type]:
            self.subscribers[event_type].remove(callback)
            self.logger.debug(f"Unsubscribed from event: {event_type}")
            
    def publish(self, event_type: str, data: Dict[str, Any]) -> None:
        """Publish an event to all subscribers"""
        event = {
            "type": event_type,
            "data": data,
            "timestamp": time.time()
        }
        self.event_queue.put(event)
        self.logger.debug(f"Published event: {event_type}")
        
    def start(self) -> None:
        """Start processing events"""
        self.running = True
        self.worker_thread = threading.Thread(target=self._process_events, daemon=True)
        self.worker_thread.start()
        self.logger.info("EventBus started")
        
    def stop(self) -> None:
        """Stop processing events"""
        self.running = False
        self.worker_thread.join(timeout=5.0)
        self.logger.info("EventBus stopped")
        
    def _process_events(self) -> None:
        """Process events from the queue"""
        while self.running:
            try:
                # Get event with timeout to check running flag periodically
                try:
                    event = self.event_queue.get(timeout=1.0)
                except queue.Empty:
                    continue
                    
                event_type = event["type"]
                
                # Process subscribers
                if event_type in self.subscribers:
                    for callback in self.subscribers[event_type]:
                        try:
                            callback(event)
                        except Exception as e:
                            self.logger.error(f"Error in event handler for {event_type}: {str(e)}")
                
                # Mark task as done
                self.event_queue.task_done()
                
            except Exception as e:
                self.logger.error(f"Error processing event: {str(e)}")
