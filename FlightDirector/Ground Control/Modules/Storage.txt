# Ground Control Storage Module

## Directory Structure
```
modules/storage/
├── __init__.py
├── buffer.py       # Memory buffer management
├── persistent.py   # Disk storage management
├── cleanup.py      # Storage maintenance
├── indexer.py      # Data indexing and search
├── compression.py  # Data compression
└── sync.py        # Cloud synchronization
```

## Core Components

### 1. Buffer Manager (buffer.py)
```python
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
```

### 2. Persistent Storage (persistent.py)
```python
import sqlite3
from pathlib import Path

class DataStore:
    """
    Manages persistent storage using SQLite.
    Handles data organization and retrieval.
    """
    def __init__(self, config: dict):
        self.db_path = Path(config['storage_path']) / 'data.db'
        self.max_size = config['max_storage_gb'] * 1024 * 1024 * 1024
        self.connection = None
        self.ensure_directory()

    async def initialize(self):
        """Set up database structure"""
        self.connection = await self._get_connection()
        await self._create_tables()

    async def store(self, data: Dict[str, Any], metadata: Dict[str, Any]) -> str:
        """Store data with metadata"""
        try:
            # Compress if needed
            if data.get('compress', False):
                data = await self._compress_data(data)

            # Store with metadata
            async with self.connection.cursor() as cursor:
                await cursor.execute("""
                    INSERT INTO data (timestamp, type, priority, data, metadata)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    metadata['timestamp'],
                    metadata['type'],
                    metadata['priority'],
                    data,
                    json.dumps(metadata)
                ))
                return cursor.lastrowid

        except Exception as e:
            raise StorageError(f"Failed to store data: {str(e)}")

    async def query(self, criteria: Dict[str, Any]) -> AsyncIterator[Dict[str, Any]]:
        """Query data based on criteria"""
        query = """
            SELECT * FROM data WHERE 1=1
        """
        params = []

        # Build query based on criteria
        if 'start_time' in criteria:
            query += " AND timestamp >= ?"
            params.append(criteria['start_time'])
        if 'end_time' in criteria:
            query += " AND timestamp <= ?"
            params.append(criteria['end_time'])
        if 'type' in criteria:
            query += " AND type = ?"
            params.append(criteria['type'])
        if 'priority' in criteria:
            query += " AND priority >= ?"
            params.append(criteria['priority'])

        async with self.connection.cursor() as cursor:
            async for row in cursor.execute(query, params):
                yield self._row_to_dict(row)
```

### 3. Cleanup Manager (cleanup.py)
```python
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
```

### 4. Data Indexer (indexer.py)
```python
class DataIndexer:
    """
    Manages data indexing for fast retrieval.
    Uses SQLite FTS for text search.
    """
    def __init__(self, connection):
        self.connection = connection
        self.indexed_fields = ['type', 'source', 'metadata']

    async def index_item(self, item_id: str, data: Dict[str, Any]):
        """Index an item for searching"""
        try:
            search_text = self._prepare_search_text(data)
            async with self.connection.cursor() as cursor:
                await cursor.execute("""
                    INSERT INTO search_index (item_id, search_text)
                    VALUES (?, ?)
                """, (item_id, search_text))
        except Exception as e:
            raise IndexError(f"Failed to index item: {str(e)}")

    async def search(self, query: str) -> List[str]:
        """Search indexed data"""
        async with self.connection.cursor() as cursor:
            results = await cursor.execute("""
                SELECT item_id FROM search_index
                WHERE search_text MATCH ?
                ORDER BY rank
            """, (query,))
            return [row[0] for row in results]
```

### 5. Compression Manager (compression.py)
```python
import lz4.frame
import json

class CompressionManager:
    """
    Handles data compression and decompression.
    Optimizes storage space.
    """
    def __init__(self, config: dict):
        self.compression_level = config.get('compression_level', 0)
        self.min_size = config.get('min_compress_size', 1024)

    async def should_compress(self, data: bytes) -> bool:
        """Determine if data should be compressed"""
        return len(data) > self.min_size

    async def compress(self, data: Dict[str, Any]) -> bytes:
        """Compress data with metadata"""
        try:
            json_data = json.dumps(data)
            if not await self.should_compress(json_data.encode()):
                return json_data.encode()

            compressed = lz4.frame.compress(
                json_data.encode(),
                compression_level=self.compression_level
            )
            return compressed
        except Exception as e:
            raise CompressionError(f"Compression failed: {str(e)}")

    async def decompress(self, data: bytes) -> Dict[str, Any]:
        """Decompress data and restore structure"""
        try:
            # Check if data is compressed
            if data.startswith(b'\x04\x22\x4D\x18'):  # LZ4 frame magic number
                decompressed = lz4.frame.decompress(data)
                return json.loads(decompressed)
            return json.loads(data)
        except Exception as e:
            raise CompressionError(f"Decompression failed: {str(e)}")
```

## Usage Example

```python
# Example storage usage
async def main():
    # Initialize storage components
    config = {
        'storage_path': '/data',
        'max_storage_gb': 32,
        'buffer_size_mb': 100,
        'cleanup_interval': 3600,
        'compression_level': 1
    }

    # Create storage manager
    storage = StorageManager(config, event_bus)
    await storage.initialize()

    # Store data example
    data = {
        'node_id': 'SPLAT-001',
        'measurements': {
            'temperature': 25.4,
            'humidity': 65
        }
    }

    metadata = {
        'timestamp': datetime.now(),
        'type': 'telemetry',
        'priority': 2
    }

    # Store with automatic buffering/persistence
    item_id = await storage.store(data, metadata)

    # Query example
    criteria = {
        'start_time': datetime.now() - timedelta(hours=1),
        'type': 'telemetry',
        'priority': 2
    }

    async for item in storage.query(criteria):
        print(f"Found: {item}")
```

## Key Features

1. Data Management:
   - Memory buffering
   - Persistent storage
   - Automatic cleanup
   - Compression

2. Performance:
   - Fast buffering
   - Efficient indexing
   - Smart compression
   - Query optimization

3. Reliability:
   - Data integrity
   - Error recovery
   - Space management
   - Backup support

4. Organization:
   - Priority handling
   - Age-based cleanup
   - Search capability
   - Metadata support
