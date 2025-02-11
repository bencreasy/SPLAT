# Ground Control Modular Architecture

## Repository Structure
```
ground_control/
├── .github/
│   └── workflows/
│       ├── test.yml
│       ├── build.yml
│       └── deploy.yml
│
├── modules/
│   ├── core/              # Core system management
│   │   ├── __init__.py
│   │   ├── system.py     # System management
│   │   ├── config.py     # Configuration handling
│   │   └── events.py     # Event system
│   │
│   ├── lora/             # LoRa communication
│   │   ├── __init__.py
│   │   ├── handler.py    # Packet handling
│   │   ├── decoder.py    # Message decoding
│   │   └── manager.py    # LoRa device management
│   │
│   ├── storage/          # Local data management
│   │   ├── __init__.py
│   │   ├── buffer.py     # Memory buffer
│   │   ├── persistent.py # Disk storage
│   │   └── cleanup.py    # Storage management
│   │
│   ├── display/          # Local display handling
│   │   ├── __init__.py
│   │   ├── lcd.py       # LCD interface
│   │   ├── led.py       # LED control
│   │   └── pages.py     # Display pages
│   │
│   ├── cloud/            # Cloud communication
│   │   ├── __init__.py
│   │   ├── sync.py      # Data synchronization
│   │   ├── pubsub.py    # Message handling
│   │   └── status.py    # Cloud status reporting
│   │
│   └── monitor/          # System monitoring
│       ├── __init__.py
│       ├── health.py     # Health checking
│       ├── metrics.py    # Metrics collection
│       └── alerts.py     # Alert generation
│
├── config/
│   ├── default.yml       # Default configuration
│   ├── modules.yml       # Module configuration
│   └── secrets.yml.enc   # Encrypted secrets
│
├── scripts/
│   ├── install.sh        # Installation script
│   ├── update.sh         # Update script
│   └── backup.sh         # Backup script
│
└── docker/               # Containerization
    ├── Dockerfile
    └── docker-compose.yml
```

## Module Communication
```python
# Core event system for inter-module communication
from dataclasses import dataclass
from typing import Any, Dict

@dataclass
class Event:
    type: str
    source: str
    data: Dict[str, Any]
    timestamp: float

class EventBus:
    def __init__(self):
        self.subscribers = {}
        
    def subscribe(self, event_type: str, callback):
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(callback)
        
    def publish(self, event: Event):
        if event.type in self.subscribers:
            for callback in self.subscribers[event.type]:
                callback(event)
```

## Module Template
```python
# Base class for all modules
class BaseModule:
    def __init__(self, event_bus, config):
        self.event_bus = event_bus
        self.config = config
        self.running = False
        
    async def start(self):
        self.running = True
        await self.setup()
        
    async def stop(self):
        self.running = False
        await self.cleanup()
        
    async def setup(self):
        raise NotImplementedError
        
    async def cleanup(self):
        raise NotImplementedError
```

## Deployment Configuration
```yaml
# docker-compose.yml
version: '3.8'

services:
  ground_control:
    build: .
    restart: always
    volumes:
      - ./config:/app/config
      - ./data:/app/data
    devices:
      - "/dev/spidev0.0:/dev/spidev0.0"
    environment:
      - GC_ENV=production
      - GC_CONFIG=/app/config/default.yml
    
  display:
    build: ./modules/display
    privileged: true
    depends_on:
      - ground_control
```

## Automated Build
```yaml
# .github/workflows/build.yml
name: Build and Test

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  build:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        
    - name: Run tests
      run: |
        pytest tests/
        
    - name: Build Docker image
      run: |
        docker build -t ground-control .
```

## Module Configuration
```yaml
# config/modules.yml
lora:
  enabled: true
  device: /dev/spidev0.0
  frequency: 915
  bandwidth: 125000
  coding_rate: 5
  spreading_factor: 7

storage:
  enabled: true
  buffer_size: 100MB
  max_storage: 1GB
  cleanup_interval: 1h

display:
  enabled: true
  type: ssd1306
  width: 128
  height: 64
  refresh_rate: 1

monitor:
  enabled: true
  check_interval: 30s
  metrics_interval: 1m
  alert_threshold: 90
```

## Local Display Interface
```python
# modules/display/pages.py
class DisplayManager:
    def __init__(self, display, event_bus):
        self.display = display
        self.event_bus = event_bus
        self.pages = {}
        self.current_page = None
        
    def add_page(self, name, page):
        self.pages[name] = page
        
    async def show_page(self, name):
        if name in self.pages:
            self.current_page = self.pages[name]
            await self.update()
            
    async def update(self):
        if self.current_page:
            await self.current_page.render(self.display)
```

## Cloud Integration
```python
# modules/cloud/sync.py
class CloudSync:
    def __init__(self, config, event_bus):
        self.config = config
        self.event_bus = event_bus
        self.queue = asyncio.Queue()
        
    async def start(self):
        while True:
            try:
                data = await self.queue.get()
                await self.send_to_cloud(data)
            except Exception as e:
                await self.handle_error(e)
                
    async def send_to_cloud(self, data):
        # Send data to Flight Director
        # Implement retry logic
        pass
```

## Health Monitoring
```python
# modules/monitor/health.py
class HealthMonitor:
    def __init__(self, config, event_bus):
        self.config = config
        self.event_bus = event_bus
        self.metrics = {}
        
    async def check_health(self):
        cpu = await self.get_cpu_usage()
        memory = await self.get_memory_usage()
        disk = await self.get_disk_usage()
        
        self.event_bus.publish(Event(
            type="health_update",
            source="monitor",
            data={
                "cpu": cpu,
                "memory": memory,
                "disk": disk
            }
        ))
```
