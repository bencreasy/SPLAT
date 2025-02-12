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
