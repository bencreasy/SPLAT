class CleanupManager:
    """
    Handles storage maintenance and cleanup.
    Ensures storage limits are respected.
    """
    def __init__(self, config: dict, event_bus):
        self.config = config
        self.event_bus = event_bus
        self.running = False

    async def start(self):
        """Start cleanup monitoring"""
        self.running = True
        asyncio.create_task(self._cleanup_loop())

    async def _cleanup_loop(self):
        """Regular cleanup check"""
        while self.running:
            try:
                await self._check_storage()
                await self._clean_old_data()
                await self._optimize_storage()
                await asyncio.sleep(self.config['cleanup_interval'])
            except Exception as e:
                await self._handle_error(e)

    async def _clean_old_data(self):
        """Remove old data based on rules"""
        rules = {
            'low': {'age': 7, 'priority': 1},    # 7 days for low priority
            'normal': {'age': 30, 'priority': 2}, # 30 days for normal
            'high': {'age': 90, 'priority': 3}    # 90 days for high
        }

        for rule in rules.values():
            await self._apply_cleanup_rule(rule)
