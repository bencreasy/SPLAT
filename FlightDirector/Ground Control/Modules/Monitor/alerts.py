from enum import Enum
from dataclasses import dataclass
from typing import Optional, List
import asyncio

class AlertSeverity(Enum):
    INFO = 1
    WARNING = 2
    ERROR = 3
    CRITICAL = 4

@dataclass
class Alert:
    """Alert information"""
    severity: AlertSeverity
    source: str
    message: str
    timestamp: float
    data: Optional[Dict[str, Any]] = None
    acknowledged: bool = False

class AlertManager:
    """
    Manages system alerts.
    Handles alert generation and distribution.
    """
    def __init__(self, config: dict, event_bus):
        self.config = config
        self.event_bus = event_bus
        self.alerts = []
        self.handlers = []
        
    async def add_alert(self, alert: Alert):
        """Add new alert"""
        self.alerts.append(alert)
        
        # Notify handlers
        for handler in self.handlers:
            try:
                await handler(alert)
            except Exception as e:
                await self._handle_handler_error(handler, e)
                
        # Publish alert event
        await self.event_bus.publish({
            'type': 'alert',
            'data': {
                'severity': alert.severity.name,
                'source': alert.source,
                'message': alert.message,
                'timestamp': alert.timestamp
            }
        })
        
        # Clean old alerts
        await self._clean_alerts()
        
    async def _clean_alerts(self):
        """Remove old acknowledged alerts"""
        current_time = time.time()
        retention = self.config['alert_retention']
        
        self.alerts = [
            alert for alert in self.alerts
            if not alert.acknowledged or
            (current_time - alert.timestamp) < retention
        ]
