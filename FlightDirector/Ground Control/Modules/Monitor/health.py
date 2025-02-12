from dataclasses import dataclass
from typing import Dict, List, Optional
from datetime import datetime
import psutil
import asyncio

@dataclass
class HealthStatus:
    """System health status"""
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    temperature: float
    network_status: bool
    last_update: datetime
    warnings: List[str]
    errors: List[str]

class HealthMonitor:
    """
    Monitors overall system health.
    Tracks critical system metrics.
    """
    def __init__(self, config: dict, event_bus):
        self.config = config
        self.event_bus = event_bus
        self.status = HealthStatus(
            cpu_usage=0.0,
            memory_usage=0.0,
            disk_usage=0.0,
            temperature=0.0,
            network_status=False,
            last_update=datetime.now(),
            warnings=[],
            errors=[]
        )
        self.thresholds = config.get('thresholds', {
            'cpu_warning': 80.0,
            'cpu_critical': 90.0,
            'memory_warning': 80.0,
            'memory_critical': 90.0,
            'disk_warning': 80.0,
            'disk_critical': 90.0,
            'temp_warning': 70.0,
            'temp_critical': 80.0
        })
        
    async def start(self):
        """Start health monitoring"""
        asyncio.create_task(self._monitor_loop())
        
    async def _monitor_loop(self):
        """Main monitoring loop"""
        while True:
            try:
                await self._check_health()
                await self._evaluate_status()
                await asyncio.sleep(self.config['check_interval'])
            except Exception as e:
                await self._handle_error(e)
                
    async def _check_health(self):
        """Collect current health metrics"""
        self.status.cpu_usage = await self._get_cpu_usage()
        self.status.memory_usage = await self._get_memory_usage()
        self.status.disk_usage = await self._get_disk_usage()
        self.status.temperature = await self._get_temperature()
        self.status.network_status = await self._check_network()
        self.status.last_update = datetime.now()
