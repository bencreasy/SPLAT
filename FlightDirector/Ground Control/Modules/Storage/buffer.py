from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime
import asyncio

@dataclass
class BufferItem:
    """Individual buffer item structure"""
    id: str
    data: Dict[str, Any]
    timestamp: datetime
    priority: int
    attempts: int = 0
    size: int = 0

class RingBuffer:
    """
    Fast, memory-based ring buffer for immediate storage.
    Handles overflow by priority.
    """
    def __init__(self, max_size_mb: int = 100):
        self.max_size = max_size_mb * 1024 * 1024  # Convert to bytes
        self.current_size = 0
        self.buffer = {}
        self.priority_queues = {1: [], 2: [], 3: [], 4: [], 5: []}
        self.lock = asyncio.Lock()

    async def push(self, item: BufferItem) -> bool:
        """Add item to buffer with priority handling"""
        async with self.lock:
            # Check if we need to make space
            if self.current_size + item.size > self.max_size:
                if not await self._make_space(item.size, item.priority):
                    return False

            # Add item
            self.buffer[item.id] = item
            self.priority_queues[item.priority].append(item.id)
            self.current_size += item.size
            return True

    async def _make_space(self, needed_size: int, min_priority: int) -> bool:
        """Clear space by removing lower priority items"""
        for priority in range(1, min_priority):
            while self.priority_queues[priority] and \
                  self.current_size + needed_size > self.max_size:
                item_id = self.priority_queues[priority].pop(0)
                item = self.buffer.pop(item_id)
                self.current_size -= item.size
                # Ensure important data is saved to disk
                if item.attempts < 3:
                    await self._save_to_disk(item)
        return self.current_size + needed_size <= self.max_size
