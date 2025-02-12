from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime
import asyncio

@dataclass
class SyncStatus:
    """Sync status information"""
    last_sync: datetime
    pending_items: int
    last_error: Optional[str]
    connected: bool
    retry_count: int

class CloudSync:
    """
    Manages data synchronization with Flight Director.
    Handles offline operation and recovery.
    """
    def __init__(self, config: dict, event_bus):
        self.config = config
        self.event_bus = event_bus
        self.status = SyncStatus(
            last_sync=datetime.now(),
            pending_items=0,
            last_error=None,
            connected=False,
            retry_count=0
        )
        self.queue = asyncio.Queue()
        self.running = False
        
    async def start(self):
        """Start sync operations"""
        self.running = True
        asyncio.create_task(self._sync_loop())
        asyncio.create_task(self._status_check_loop())
        
    async def _sync_loop(self):
        """Main sync loop"""
        while self.running:
            try:
                if self.status.connected:
                    item = await self.queue.get()
                    await self._send_to_cloud(item)
                    self.status.last_sync = datetime.now()
                    self.status.pending_items = self.queue.qsize()
                else:
                    await asyncio.sleep(self.config['retry_interval'])
                    
            except Exception as e:
                await self._handle_error(e)
                
    async def _send_to_cloud(self, item: Dict[str, Any]):
        """Send data to Flight Director"""
        try:
            response = await self.pubsub.publish(
                topic=item['topic'],
                data=item['data'],
                retry=self.config['retry_attempts']
            )
            await self._handle_response(response)
            
        except Exception as e:
            if self._should_retry(e):
                await self._requeue_item(item)
            else:
                await self._handle_fatal_error(e, item)
