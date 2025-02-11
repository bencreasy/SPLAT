# Ground Control Monitor Module

## Directory Structure
```
modules/monitor/
├── __init__.py
├── health.py       # System health monitoring
├── metrics.py      # Metrics collection
├── alerts.py       # Alert management
├── probes/         # System probes
│   ├── __init__.py
│   ├── system.py   # System metrics
│   ├── network.py  # Network metrics
│   └── hardware.py # Hardware metrics
└── collectors/     # Data collectors
    ├── __init__.py
    ├── performance.py
    └── resources.py
```

## Core Components

### 1. Health Monitor (health.py)
```python
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
```

### 2. Metrics Collector (metrics.py)
```python
from dataclasses import dataclass
from typing import Dict, Any
import time

@dataclass
class MetricPoint:
    """Single metric measurement"""
    value: float
    timestamp: float
    labels: Dict[str, str]

class MetricsCollector:
    """
    Collects and manages system metrics.
    Handles metric storage and aggregation.
    """
    def __init__(self, config: dict):
        self.config = config
        self.metrics = {}
        self.collectors = self._setup_collectors()
        
    def _setup_collectors(self):
        """Initialize metric collectors"""
        return {
            'system': SystemCollector(),
            'network': NetworkCollector(),
            'hardware': HardwareCollector()
        }
        
    async def collect(self):
        """Collect all metrics"""
        timestamp = time.time()
        
        for name, collector in self.collectors.items():
            try:
                metrics = await collector.collect()
                self._store_metrics(name, metrics, timestamp)
            except Exception as e:
                await self._handle_collector_error(name, e)
                
    def _store_metrics(self, source: str, metrics: Dict[str, float], 
                      timestamp: float):
        """Store collected metrics"""
        for name, value in metrics.items():
            metric_key = f"{source}_{name}"
            if metric_key not in self.metrics:
                self.metrics[metric_key] = []
                
            self.metrics[metric_key].append(MetricPoint(
                value=value,
                timestamp=timestamp,
                labels={'source': source}
            ))
            
            # Prune old metrics
            self._prune_metrics(metric_key)
```

### 3. Alert Manager (alerts.py)
```python
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
```

### 4. System Probe Example (probes/system.py)
```python
class SystemProbe:
    """
    Collects system-level metrics.
    CPU, memory, disk, etc.
    """
    def __init__(self):
        self.cpu_count = psutil.cpu_count()
        
    async def get_cpu_metrics(self) -> Dict[str, float]:
        """Collect CPU metrics"""
        return {
            'usage_percent': psutil.cpu_percent(interval=1),
            'load_1min': psutil.getloadavg()[0],
            'load_5min': psutil.getloadavg()[1],
            'load_15min': psutil.getloadavg()[2]
        }
        
    async def get_memory_metrics(self) -> Dict[str, float]:
        """Collect memory metrics"""
        mem = psutil.virtual_memory()
        return {
            'total': mem.total,
            'available': mem.available,
            'used': mem.used,
            'percent': mem.percent
        }
        
    async def get_disk_metrics(self) -> Dict[str, float]:
        """Collect disk metrics"""
        disk = psutil.disk_usage('/')
        return {
            'total': disk.total,
            'used': disk.used,
            'free': disk.free,
            'percent': disk.percent
        }
```

### 5. Performance Collector (collectors/performance.py)
```python
class PerformanceCollector:
    """
    Collects performance metrics.
    Tracks system performance indicators.
    """
    def __init__(self):
        self.history = collections.deque(maxlen=100)
        
    async def collect(self) -> Dict[str, float]:
        """Collect performance metrics"""
        metrics = {}
        
        # CPU Performance
        metrics.update(await self._get_cpu_performance())
        
        # Memory Performance
        metrics.update(await self._get_memory_performance())
        
        # I/O Performance
        metrics.update(await self._get_io_performance())
        
        # Store history
        self.history.append((time.time(), metrics))
        
        return metrics
        
    async def _get_cpu_performance(self) -> Dict[str, float]:
        """Collect CPU performance metrics"""
        cpu_times = psutil.cpu_times_percent()
        return {
            'cpu_user': cpu_times.user,
            'cpu_system': cpu_times.system,
            'cpu_idle': cpu_times.idle,
            'cpu_iowait': getattr(cpu_times, 'iowait', 0)
        }
```

## Usage Example

```python
# Example monitoring usage
async def main():
    # Initialize monitoring
    config = {
        'check_interval': 60,
        'alert_retention': 86400,  # 24 hours
        'thresholds': {
            'cpu_warning': 80.0,
            'memory_warning': 80.0,
            'disk_warning': 80.0,
            'temp_warning': 70.0
        }
    }
    
    # Create monitors
    health = HealthMonitor(config, event_bus)
    metrics = MetricsCollector(config)
    alerts = AlertManager(config, event_bus)
    
    # Start monitoring
    await health.start()
    
    # Example alert handler
    async def handle_alert(alert: Alert):
        if alert.severity >= AlertSeverity.ERROR:
            # Send to cloud
            await cloud.send_alert(alert)
            # Update local display
            await display.show_alert(alert)
    
    # Register alert handler
    alerts.handlers.append(handle_alert)
```

## Key Features

1. Health Monitoring:
   - System metrics
   - Performance tracking
   - Resource usage
   - Temperature monitoring

2. Metrics Collection:
   - Various collectors
   - Metric aggregation
   - Historical data
   - Performance analysis

3. Alert Management:
   - Multiple severities
   - Alert distribution
   - Handler system
   - Alert history

4. Reliability:
   - Error handling
   - Data persistence
   - Performance impact
   - Resource efficiency
