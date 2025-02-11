# Ground Control Cloud Module

## Directory Structure
```
modules/cloud/
├── __init__.py
├── sync.py        # Data synchronization
├── pubsub.py      # Message handling
├── status.py      # Cloud status reporting
├── auth.py        # Authentication
├── retry.py       # Retry handling
└── queue.py       # Message queuing
```

## Core Components

### 1. Cloud Sync Manager (sync.py)
```python
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
```

### 2. Pub/Sub Handler (pubsub.py)
```python
from google.cloud import pubsub_v1
import json

class PubSubHandler:
    """
    Handles pub/sub communication with GCP.
    Manages message topics and subscriptions.
    """
    def __init__(self, config: dict):
        self.config = config
        self.publisher = pubsub_v1.PublisherClient()
        self.subscriber = pubsub_v1.SubscriberClient()
        self.topics = {}
        
    async def initialize(self):
        """Initialize pub/sub connections"""
        # Set up standard topics
        self.topics = {
            'telemetry': self._get_topic_path('telemetry'),
            'status': self._get_topic_path('status'),
            'alerts': self._get_topic_path('alerts'),
            'commands': self._get_topic_path('commands')
        }
        
        # Start command subscription
        await self._start_command_subscription()
        
    async def publish(self, topic: str, data: Dict[str, Any], 
                     retry: int = 3) -> bool:
        """Publish message to topic"""
        if topic not in self.topics:
            raise ValueError(f"Unknown topic: {topic}")
            
        try:
            # Prepare message
            message = json.dumps(data).encode('utf-8')
            
            # Publish with retry
            for attempt in range(retry):
                try:
                    future = self.publisher.publish(
                        self.topics[topic],
                        message
                    )
                    return await future
                except Exception as e:
                    if attempt == retry - 1:
                        raise
                    await asyncio.sleep(2 ** attempt)
                    
        except Exception as e:
            raise PublishError(f"Failed to publish to {topic}: {str(e)}")
```

### 3. Status Reporter (status.py)
```python
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
```

### 4. Authentication Manager (auth.py)
```python
from google.oauth2 import service_account
import jwt

class AuthManager:
    """
    Handles authentication with GCP.
    Manages credentials and tokens.
    """
    def __init__(self, config: dict):
        self.config = config
        self.credentials = None
        self.token = None
        
    async def initialize(self):
        """Initialize authentication"""
        try:
            # Load service account credentials
            self.credentials = service_account.Credentials.from_service_account_file(
                self.config['credentials_path'],
                scopes=self.config['scopes']
            )
            
            # Get initial token
            await self.refresh_token()
            
        except Exception as e:
            raise AuthError(f"Authentication failed: {str(e)}")
            
    async def refresh_token(self):
        """Refresh authentication token"""
        try:
            if self.credentials.expired:
                self.credentials.refresh()
            self.token = self.credentials.token
            
        except Exception as e:
            raise AuthError(f"Token refresh failed: {str(e)}")
```

### 5. Retry Handler (retry.py)
```python
from dataclasses import dataclass
import asyncio

@dataclass
class RetryConfig:
    """Retry configuration"""
    max_attempts: int
    base_delay: float
    max_delay: float
    jitter: float

class RetryHandler:
    """
    Handles retry logic for failed operations.
    Implements exponential backoff.
    """
    def __init__(self, config: RetryConfig):
        self.config = config
        
    async def execute(self, operation, *args, **kwargs):
        """Execute operation with retry"""
        last_error = None
        
        for attempt in range(self.config.max_attempts):
            try:
                return await operation(*args, **kwargs)
                
            except Exception as e:
                last_error = e
                if not self._should_retry(e):
                    raise
                    
                delay = self._calculate_delay(attempt)
                await asyncio.sleep(delay)
                
        raise MaxRetriesError(f"Max retries exceeded: {str(last_error)}")
        
    def _calculate_delay(self, attempt: int) -> float:
        """Calculate retry delay with exponential backoff"""
        delay = min(
            self.config.base_delay * (2 ** attempt),
            self.config.max_delay
        )
        jitter = random.uniform(0, self.config.jitter)
        return delay + jitter
```

## Usage Example

```python
# Example cloud module usage
async def main():
    # Initialize cloud components
    config = {
        'project_id': 'splat-project',
        'retry_interval': 30,
        'retry_attempts': 3,
        'status_interval': 60,
        'credentials_path': 'path/to/credentials.json'
    }
    
    cloud = CloudSync(config, event_bus)
    await cloud.start()
    
    # Send telemetry example
    telemetry = {
        'node_id': 'SPLAT-001',
        'timestamp': datetime.now().isoformat(),
        'data': {
            'temperature': 25.4,
            'humidity': 65
        }
    }
    
    await cloud.queue.put({
        'topic': 'telemetry',
        'data': telemetry
    })
    
    # Handle command subscription
    async def handle_command(message):
        data = json.loads(message.data)
        await process_command(data)
        message.ack()
        
    await cloud.pubsub.subscribe('commands', handle_command)
```

## Key Features

1. Data Synchronization:
   - Reliable delivery
   - Offline operation
   - Automatic recovery
   - Queue management

2. Communication:
   - Pub/Sub messaging
   - Status reporting
   - Command handling
   - Error management

3. Security:
   - Authentication
   - Token management
   - Secure transport
   - Error handling

4. Reliability:
   - Retry logic
   - Queue persistence
   - Status monitoring
   - Error recovery
