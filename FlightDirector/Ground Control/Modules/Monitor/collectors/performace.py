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
