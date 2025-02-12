class StatusReporter:
    """
    Reports Ground Control status to Flight Director.
    Handles health checks and metrics.
    """
    def __init__(self, config: dict, pubsub: PubSubHandler):
        self.config = config
        self.pubsub = pubsub
        self.metrics = {}
        
    async def start(self):
        """Start status reporting"""
        asyncio.create_task(self._report_loop())
        
    async def _report_loop(self):
        """Regular status reporting"""
        while True:
            try:
                status = await self._collect_status()
                await self.pubsub.publish(
                    topic='status',
                    data=status
                )
                await asyncio.sleep(self.config['status_interval'])
                
            except Exception as e:
                await self._handle_error(e)
                
    async def _collect_status(self) -> Dict[str, Any]:
        """Collect current status information"""
        return {
            'timestamp': datetime.now().isoformat(),
            'version': self.config['version'],
            'uptime': self._get_uptime(),
            'memory': self._get_memory_usage(),
            'cpu': self._get_cpu_usage(),
            'disk': self._get_disk_usage(),
            'node_count': len(self.metrics.get('nodes', [])),
            'queue_size': self.metrics.get('queue_size', 0),
            'last_sync': self.metrics.get('last_sync'),
            'errors': self.metrics.get('errors', [])
        }
